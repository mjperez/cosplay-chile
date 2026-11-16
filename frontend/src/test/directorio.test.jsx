import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { USUARIO, montar, simularApi } from './utilidades'

const ITEM = {
  id: 'd1', tipo: 'PROVEEDOR', nombre: 'Taller Aurora', descripcion: 'Armaduras en EVA.', region: 'RM', comuna: 'Santiago',
  imagen_url: null, especialidades: ['SASTRERIA'], tipos_producto: null, alcance: null, envia_a_chile: true, tienda_fisica: true,
  plataforma: null, precio_desde: 15000, precio_hasta: 90000, lat: -33.45, lng: -70.66, promedio: 4.8, total_resenas: 2,
}
const COMUNIDAD = { ...ITEM, id: 'k1', tipo: 'COMUNIDAD', nombre: 'Cosplay Valparaíso', region: 'VA', plataforma: 'Instagram', especialidades: null }
const PAGINA = (items) => ({ items, total: items.length, pagina: 1, por_pagina: 12, paginas: 1 })
const PUNTOS = [
  { id: 'd1', tipo: 'PROVEEDOR', nombre: 'Taller Aurora', lat: -33.45, lng: -70.66, region: 'RM', comuna: 'Santiago' },
  { id: 'd2', tipo: 'PROVEEDOR', nombre: 'Sastrería Sur', lat: -36.8, lng: -73.05, region: 'BI', comuna: 'Concepción' },
]
const DETALLE = {
  ...ITEM, servicios: ['Armadura completa'], portafolio: [], contacto: '@taller.aurora', sitio_web: 'https://aurora.example',
  direccion: null, perfil_usuario_id: null, es_favorito: false, puede_resenar: true, ya_resenado: false,
  resenas: [{ id: 'r1', calificacion: 5, comentario: 'Entregó a tiempo.', created_at: '2026-11-01T10:00:00Z', autor: { id: 'u3', nombre: 'Kuro' } }],
}

function apiDirectorio(extra = {}, opciones) {
  return simularApi(
    {
      '/api/directorio': (u) => (u.searchParams.get('tipo') === 'COMUNIDAD' ? PAGINA([COMUNIDAD]) : PAGINA([ITEM])),
      '/api/directorio/mapa': PUNTOS,
      '/api/directorio/d1': DETALLE,
      ...extra,
    },
    opciones,
  )
}

describe('Directorio', () => {
  it('muestra profesionales con valoración, ubicación y precio', async () => {
    apiDirectorio()
    montar('/directorio')
    expect(screen.getByRole('tab', { name: 'Profesionales' })).toHaveAttribute('aria-selected', 'true')
    const resultados = await screen.findByRole('region', { name: 'Resultados' })
    expect(await within(resultados).findByRole('heading', { name: 'Taller Aurora' })).toBeInTheDocument()
    expect(within(resultados).getByText(/Desde/)).toHaveTextContent('15.000')
    expect(within(resultados).getByLabelText('4,8 de 5 estrellas, 2 reseñas')).toBeInTheDocument()
  })

  it('el mapa esquemático filtra por región', async () => {
    const fetchMock = apiDirectorio()
    montar('/directorio')
    const pin = await screen.findByRole('button', { name: /Filtrar por región Biobío/ })
    await userEvent.click(pin)
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('region=BI')
    await waitFor(() => expect(fetchMock.mock.calls.some(([u]) => String(u).startsWith('/api/directorio?tipo=PROVEEDOR&region=BI'))).toBe(true))
    expect(screen.getByRole('button', { name: /Filtrar por región Biobío/ })).toHaveAttribute('aria-pressed', 'true')
  })

  it('las pestañas cambian de sección y se recorren con flechas', async () => {
    apiDirectorio()
    montar('/directorio')
    const tab = screen.getByRole('tab', { name: 'Profesionales' })
    tab.focus()
    await userEvent.keyboard('{ArrowRight}')
    expect(screen.getByRole('tab', { name: 'Tiendas · dónde comprar' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('button', { name: 'Internacionales con envío a Chile' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: 'Comunidades por región' }))
    expect(await screen.findByRole('link', { name: /Ver comunidad.*Cosplay Valparaíso/ })).toHaveAttribute('href', '/directorio/k1')
  })

  it('en pantallas pequeñas «Ver ficha» abre la ficha completa', async () => {
    apiDirectorio()
    montar('/directorio')
    await userEvent.click(await screen.findByRole('button', { name: 'Ver ficha: Taller Aurora' }))
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('/directorio/d1')
    expect(await screen.findByRole('heading', { level: 1, name: 'Taller Aurora' })).toBeInTheDocument()
  })
})

describe('Ficha del directorio', () => {
  it('muestra precios, servicios, contacto y reseñas', async () => {
    apiDirectorio()
    montar('/directorio/d1')
    expect(await screen.findByRole('heading', { level: 1, name: 'Taller Aurora' })).toBeInTheDocument()
    expect(screen.getByText('Armadura completa')).toBeInTheDocument()
    expect(screen.getByText('@taller.aurora')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Sitio web o red social/ })).toHaveAttribute('href', 'https://aurora.example')
    expect(screen.getByText('Entregó a tiempo.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Inicia sesión' })).toBeInTheDocument()
  })

  it('con sesión permite publicar una reseña (RF-19)', async () => {
    const fetchMock = apiDirectorio(
      { 'POST /api/directorio/d1/resenas': { status: 201, cuerpo: { id: 'r2', calificacion: 4, comentario: 'Muy bien', created_at: '2026-11-02T10:00:00Z', autor: null } } },
      { usuario: USUARIO },
    )
    montar('/directorio/d1')
    await userEvent.click(await screen.findByRole('radio', { name: '4 de 5 estrellas' }))
    await userEvent.type(screen.getByLabelText(/Tu reseña/), 'Muy bien')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar reseña' }))
    await waitFor(() => {
      const post = fetchMock.mock.calls.find(([u, o]) => u === '/api/directorio/d1/resenas' && o?.method === 'POST')
      expect(JSON.parse(post[1].body)).toEqual({ calificacion: 4, comentario: 'Muy bien' })
    })
  })

  it('sin calificación avisa antes de enviar', async () => {
    apiDirectorio({}, { usuario: USUARIO })
    montar('/directorio/d1')
    await userEvent.click(await screen.findByRole('button', { name: 'Enviar reseña' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Elige una calificación de 1 a 5 estrellas.')
  })
})
