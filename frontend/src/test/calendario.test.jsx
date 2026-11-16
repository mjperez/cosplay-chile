import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { USUARIO, montar, simularApi } from './utilidades'

const EV = (id, nombre, fecha, tipo, region, extra = {}) => ({
  id, nombre, descripcion: '', tipo, fecha_inicio: fecha, fecha_fin: null, lugar: 'Recinto', comuna: 'Ciudad', region,
  lat: null, lng: null, enlace_oficial: 'https://evento.example', imagen_url: null, imagen_alt: null, estado: 'PUBLICADO',
  created_at: '2026-11-01T10:00:00Z', ...extra,
})
const EVENTOS = [
  EV('e1', 'Meetup de diciembre', '2026-12-05', 'MEETUP', 'VA'),
  EV('e2', 'Concurso regional', '2026-12-12', 'CONCURSO', 'RM'),
  EV('e3', 'Feria de creadores', '2026-12-12', 'CONVENCION', 'RM', { fecha_fin: '2026-12-13' }),
]
const PAGINA = (items) => ({ items, total: items.length, pagina: 1, por_pagina: 100, paginas: 1 })

function apiCalendario(extra = {}, opciones) {
  return simularApi(
    {
      '/api/eventos': (u) => PAGINA(EVENTOS.filter((e) => !u.searchParams.get('tipo') || e.tipo === u.searchParams.get('tipo'))),
      ...extra,
    },
    opciones,
  )
}

describe('Calendario', () => {
  it('pide el mes completo y muestra la lista de eventos del mes', async () => {
    const fetchMock = apiCalendario()
    montar('/calendario?mes=2026-12')
    expect(screen.getByRole('heading', { name: 'Diciembre 2026' })).toBeInTheDocument()
    const lista = screen.getByRole('region', { name: 'Eventos de diciembre' })
    expect(await within(lista).findByRole('link', { name: 'Meetup de diciembre' })).toHaveAttribute('href', '/calendario/e1')
    expect(within(lista).getByText('3 eventos')).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([u]) => String(u).includes('desde=2026-12-01&hasta=2026-12-31'))).toBe(true)
    expect(within(lista).getAllByRole('link', { name: /Sitio oficial y entradas/ })[0]).toHaveAttribute('href', 'https://evento.example')
  })

  it('al elegir un día muestra solo sus eventos, incluidos los de varios días', async () => {
    apiCalendario()
    montar('/calendario?mes=2026-12')
    await screen.findAllByRole('link', { name: 'Meetup de diciembre' })
    await userEvent.click(screen.getByRole('button', { name: /domingo 13 de diciembre, 1 evento/ }))
    const lista = screen.getByRole('region', { name: 'Eventos del 13 de diciembre' })
    expect(within(lista).getByRole('link', { name: 'Feria de creadores' })).toBeInTheDocument()
    expect(within(lista).queryByRole('link', { name: 'Concurso regional' })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Ver todo el mes' }))
    expect(screen.getByRole('region', { name: 'Eventos de diciembre' })).toBeInTheDocument()
  })

  it('filtra por región con chips de las regiones que tienen eventos', async () => {
    apiCalendario()
    montar('/calendario?mes=2026-12')
    const grupo = screen.getByRole('group', { name: 'Región' })
    await userEvent.click(await within(grupo).findByRole('button', { name: 'Valparaíso' }))
    const lista = screen.getByRole('region', { name: 'Eventos de diciembre' })
    expect(within(lista).getByText('1 evento')).toBeInTheDocument()
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('region=VA')
  })

  it('navega entre meses', async () => {
    apiCalendario()
    montar('/calendario?mes=2026-12')
    await userEvent.click(screen.getByRole('button', { name: 'Mes siguiente' }))
    expect(screen.getByRole('heading', { name: 'Enero 2027' })).toBeInTheDocument()
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('mes=2027-01')
  })

  it('con sesión envía la sugerencia de evento (RF-17)', async () => {
    const fetchMock = apiCalendario(
      { 'POST /api/eventos/sugerir': { status: 201, cuerpo: EV('n1', 'Convención de primavera', '2027-01-20', 'CONVENCION', 'AR', { estado: 'PENDIENTE' }) } },
      { usuario: USUARIO },
    )
    montar('/calendario?mes=2026-12')
    const form = await screen.findByRole('form', { name: 'Sugerir un evento' })
    await userEvent.type(within(form).getByLabelText(/^Nombre del evento/), 'Convención de primavera')
    await userEvent.type(within(form).getByLabelText(/^Fecha\s*\*?$/), '2027-01-20')
    await userEvent.type(within(form).getByLabelText(/^Lugar o recinto/), 'Gimnasio municipal')
    await userEvent.click(within(form).getByRole('button', { name: 'Enviar sugerencia' }))
    expect(await screen.findByText(/quedó pendiente de revisión/)).toBeInTheDocument()
    const post = fetchMock.mock.calls.find(([u, o]) => u === '/api/eventos/sugerir' && o?.method === 'POST')
    expect(JSON.parse(post[1].body)).toMatchObject({ nombre: 'Convención de primavera', fecha_inicio: '2027-01-20', lugar: 'Gimnasio municipal' })
  })

  it('visitante ve el acceso para sugerir', () => {
    apiCalendario()
    montar('/calendario?mes=2026-12')
    expect(screen.getByRole('link', { name: 'Ingresar para sugerir' })).toBeInTheDocument()
  })
})

describe('Detalle de evento', () => {
  it('permite marcar «Asistiré» con sesión', async () => {
    const fetchMock = apiCalendario(
      {
        '/api/eventos/e1': { ...EVENTOS[0], es_favorito: false, asistire: false, asistentes: 2 },
        'POST /api/eventos/e1/asistir': { asistire: true, asistentes: 3 },
      },
      { usuario: USUARIO },
    )
    montar('/calendario/e1')
    const boton = await screen.findByRole('button', { name: 'Asistiré' })
    expect(screen.getByText('2 personas de la comunidad asistirán')).toBeInTheDocument()
    await userEvent.click(boton)
    await waitFor(() => expect(boton).toHaveAttribute('aria-pressed', 'true'))
    expect(screen.getByText('3 personas de la comunidad asistirán')).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([u, o]) => u === '/api/eventos/e1/asistir' && o?.method === 'POST')).toBe(true)
  })
})
