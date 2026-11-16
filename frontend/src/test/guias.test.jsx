import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { USUARIO, montar, simularApi } from './utilidades'

const CATEGORIAS = [
  { id: 'c1', slug: 'props-armaduras', nombre: 'Props y armaduras' },
  { id: 'c2', slug: 'maquillaje-pelucas', nombre: 'Maquillaje y pelucas' },
]
const GUIA = {
  id: 'g1', tipo: 'GUIA', titulo: 'Tu primera armadura en EVA', descripcion: 'Brazal de goma EVA.', nivel: 'PRINCIPIANTE',
  estado: 'PUBLICADO', categoria: CATEGORIAS[0], autor: { id: 'u2', nombre: 'Matías Soto' }, imagen_url: '/media/g.svg',
  imagen_alt: 'Brazal pintado', created_at: '2026-11-01T10:00:00Z',
}
const PAGINA = (items) => ({ items, total: items.length, pagina: 1, por_pagina: 12, paginas: 1 })

function apiGuias() {
  return simularApi({
    '/api/categorias': CATEGORIAS,
    '/api/contenidos': (u) => (u.searchParams.get('tipo') === 'ENTREVISTA' ? PAGINA([]) : PAGINA([GUIA])),
  })
}

describe('Guías', () => {
  it('lista guías reales con nivel, categoría y acciones', async () => {
    apiGuias()
    montar('/guias')
    expect(screen.getByRole('heading', { level: 1, name: 'Aprende cosplay paso a paso' })).toBeInTheDocument()
    const lista = await screen.findByRole('region', { name: 'Guías' })
    const tarjeta = await within(lista).findByRole('article')
    expect(within(tarjeta).getByRole('heading', { name: GUIA.titulo })).toBeInTheDocument()
    expect(within(tarjeta).getByText('Principiante')).toBeInTheDocument()
    expect(within(tarjeta).getByRole('link', { name: /Inicia sesión para guardar en favoritos/ })).toBeInTheDocument()
    expect(within(tarjeta).getByRole('button', { name: /Compartir en redes sociales/ })).toBeInTheDocument()
    expect(screen.getByText('1 guía')).toBeInTheDocument()
  })

  it('los chips de filtro cambian la consulta a la API', async () => {
    const fetchMock = apiGuias()
    montar('/guias')
    const grupo = await screen.findByRole('group', { name: 'Nivel' })
    const chip = within(grupo).getByRole('button', { name: 'Avanzado' })
    await userEvent.click(chip)
    expect(chip).toHaveAttribute('aria-pressed', 'true')
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/api/contenidos?nivel=AVANZADO'))).toBe(true),
    )
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('/guias?nivel=AVANZADO')
  })

  it('marca como favoritas las guías guardadas y permite quitarlas', async () => {
    const fetchMock = simularApi(
      {
        '/api/categorias': CATEGORIAS,
        '/api/contenidos': PAGINA([GUIA]),
        '/api/favoritos/ids': { CONTENIDO: ['g1'], DIRECTORIO: [], EVENTO: [] },
        'DELETE /api/favoritos/CONTENIDO/g1': { mensaje: 'Quitado de tus favoritos' },
      },
      { usuario: USUARIO },
    )
    montar('/guias')
    const lista = await screen.findByRole('region', { name: 'Guías' })
    const corazon = await within(lista).findByRole('button', { name: /Guardar en favoritos: Tu primera armadura/ })
    await waitFor(() => expect(corazon).toHaveAttribute('aria-pressed', 'true'))
    await userEvent.click(corazon)
    await waitFor(() => expect(corazon).toHaveAttribute('aria-pressed', 'false'))
    expect(fetchMock.mock.calls.some(([url, o]) => url === '/api/favoritos/CONTENIDO/g1' && o?.method === 'DELETE')).toBe(true)
  })

  it('compartir ofrece enlaces de WhatsApp, X y Facebook (RF-05)', async () => {
    apiGuias()
    montar('/guias')
    const lista = await screen.findByRole('region', { name: 'Guías' })
    await userEvent.click(await within(lista).findByRole('button', { name: /Compartir en redes sociales/ }))
    const wa = screen.getByRole('link', { name: /WhatsApp/ })
    expect(wa.getAttribute('href')).toContain('https://wa.me/?text=')
    expect(wa.getAttribute('href')).toContain(encodeURIComponent('/guias/g1'))
    expect(screen.getByRole('link', { name: /Facebook/ })).toBeInTheDocument()
  })

  it('las preguntas frecuentes funcionan como acordeón', async () => {
    apiGuias()
    montar('/guias')
    const boton = screen.getByRole('button', { name: '¿Cuánto cuesta hacer un cosplay?' })
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText(/precios en pesos chilenos/)).toBeVisible()
  })

  it('el envío de tutorial pide iniciar sesión a visitantes', () => {
    apiGuias()
    montar('/guias')
    expect(screen.getByRole('link', { name: 'Inicia sesión para enviar' })).toHaveAttribute('href', '/ingresar?siguiente=/guias/publicar')
  })
})

describe('Detalle de guía', () => {
  it('muestra pasos y materiales', async () => {
    simularApi({
      '/api/contenidos/g1': { ...GUIA, cuerpo: 'Intro', pasos: ['Cortar', 'Sellar'], materiales: ['Goma EVA'], es_favorito: false },
    })
    montar('/guias/g1')
    expect(await screen.findByRole('heading', { level: 1, name: GUIA.titulo })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Paso a paso' })).toBeInTheDocument()
    expect(screen.getByText('Sellar')).toBeInTheDocument()
    expect(screen.getByText('Goma EVA')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Inicia sesión para descargar/ })).toBeInTheDocument()
  })

  it('muestra 404 si la guía no existe', async () => {
    simularApi({})
    montar('/guias/no-existe')
    expect(await screen.findByRole('heading', { name: 'Guía no encontrada' })).toBeInTheDocument()
  })
})

describe('Publicar tutorial (UC6)', () => {
  it('envía el tutorial y muestra que quedó pendiente', async () => {
    const fetchMock = simularApi(
      {
        '/api/categorias': CATEGORIAS,
        'POST /api/contenidos': {
          status: 201,
          cuerpo: { mensaje: 'Tu tutorial quedó pendiente de revisión.', contenido: { ...GUIA, id: 'nuevo', estado: 'PENDIENTE' } },
        },
      },
      { usuario: USUARIO },
    )
    montar('/guias/publicar')
    await userEvent.type(await screen.findByLabelText(/^Título/), 'Guantes articulados en EVA')
    await userEvent.type(screen.getByLabelText(/^Descripción breve/), 'Cómo hacer guantes articulados.')
    await waitFor(() => expect(screen.getByRole('option', { name: 'Props y armaduras' })).toBeInTheDocument())
    await userEvent.selectOptions(screen.getByLabelText(/^Categoría/), 'c1')
    await userEvent.type(screen.getByLabelText(/^Materiales/), 'Goma EVA')
    await userEvent.type(screen.getByLabelText(/^Pasos/), 'Cortar')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar a revisión' }))
    expect(await screen.findByText('Tu tutorial quedó pendiente de revisión.')).toBeInTheDocument()
    const llamada = fetchMock.mock.calls.find(([url, o]) => url === '/api/contenidos' && o?.method === 'POST')
    expect(JSON.parse(llamada[1].body)).toMatchObject({ titulo: 'Guantes articulados en EVA', categoria_id: 'c1', pasos: ['Cortar'], materiales: ['Goma EVA'] })
  })

  it('sin sesión redirige a ingresar', async () => {
    simularApi({ '/api/categorias': CATEGORIAS })
    montar('/guias/publicar')
    await waitFor(() => expect(screen.getByTestId('ubicacion')).toHaveTextContent('/ingresar?siguiente=%2Fguias%2Fpublicar'))
  })
})
