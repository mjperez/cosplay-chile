import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { USUARIO, montar, simularApi } from './utilidades'

const FOROS = [
  { id: 'f1', titulo: 'Dudas de principiantes', slug: 'principiantes', categoria: 'Preguntas básicas', temas: 3, ultima_actividad: null },
  { id: 'f2', titulo: 'Historias de cosplayers', slug: 'historias', categoria: 'Cuéntanos tu historia', temas: 1, ultima_actividad: null },
]
const TEMA = {
  id: 't1', titulo: '¿Qué personaje elegir?', autor: { id: 'u1', nombre: 'Camila Rojas' }, created_at: new Date().toISOString(),
  respuestas: 2, tiene_imagen: false, foro_slug: 'principiantes', foro_titulo: 'Dudas de principiantes',
}
const DESAFIO = { id: 'd1', titulo: 'Reinterpreta un clásico', descripcion: 'Con materiales reutilizados.', mes: 11, anio: 2026, abierto: true, ganador: null, participaciones: 4 }
const PARTICIPACION = {
  id: 'p1', titulo: 'Hechicera reciclada', descripcion: '', autor: { id: 'u2', nombre: 'Valentina' }, imagen_url: '/media/p.svg',
  imagen_alt: 'Cosplayer con sombrero', credito_fotografo: '@astra', credito_cosplayer: '@runa', created_at: '2026-11-10T10:00:00Z',
}

function apiComunidad(extra = {}, opciones) {
  return simularApi(
    {
      '/api/foros': FOROS,
      '/api/temas/recientes': [TEMA],
      '/api/foros/historias/temas': { items: [], total: 0, pagina: 1, por_pagina: 20, paginas: 0 },
      '/api/desafios': [DESAFIO],
      '/api/inicio': { trajes_recientes: [PARTICIPACION] },
      ...extra,
    },
    opciones,
  )
}

describe('Comunidad y foro', () => {
  it('muestra desafío del mes, foros, temas y galería con créditos', async () => {
    apiComunidad()
    montar('/comunidad')
    expect(await screen.findByRole('heading', { name: 'Reinterpreta un clásico' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Participar en el desafío' })).toHaveAttribute('href', '/desafios/d1#participar')
    const foros = screen.getByRole('navigation', { name: 'Foros por tema' })
    expect(within(foros).getByRole('link', { name: /Todos/ })).toHaveAttribute('aria-current', 'page')
    expect(await within(foros).findByRole('link', { name: /Historias de cosplayers/ })).toHaveAttribute('href', '/comunidad/historias')
    expect(await screen.findByRole('link', { name: '¿Qué personaje elegir?' })).toHaveAttribute('href', '/comunidad/temas/t1')
    expect(screen.getByText('Cosplay: @runa')).toBeInTheDocument()
    expect(screen.getByText('Foto: @astra')).toBeInTheDocument()
  })

  it('el foro elegido carga sus temas y queda marcado', async () => {
    const fetchMock = apiComunidad()
    montar('/comunidad/historias')
    expect(await screen.findByText('Aún no hay temas en este foro. ¡Abre el primero!')).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([u]) => String(u).startsWith('/api/foros/historias/temas'))).toBe(true)
    const foros = screen.getByRole('navigation', { name: 'Foros por tema' })
    expect(await within(foros).findByRole('link', { name: /Historias de cosplayers/ })).toHaveAttribute('aria-current', 'page')
  })

  it('visitante ve el acceso para crear tema y la invitación en notificaciones', async () => {
    apiComunidad()
    montar('/comunidad')
    expect(screen.getByRole('link', { name: /Crear un tema nuevo… \(requiere sesión\)/ })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Notificaciones/ })).toBeInTheDocument()
  })

  it('con sesión publica un tema desde el compositor (RF-23)', async () => {
    const fetchMock = apiComunidad(
      {
        'POST /api/foros/principiantes/temas': { status: 201, cuerpo: { id: 'nuevo' } },
        '/api/temas/nuevo': {
          id: 'nuevo', titulo: 'Mi primer cosplay', contenido: 'Hola comunidad, empiezo ahora.', autor: { id: 'u1', nombre: 'Camila' },
          created_at: new Date().toISOString(), foro: FOROS[0], imagen_url: null, imagen_alt: null, credito_fotografo: null,
          credito_cosplayer: null, oculto: false, respuestas: [],
        },
      },
      { usuario: USUARIO },
    )
    montar('/comunidad')
    await userEvent.click(await screen.findByRole('button', { name: /Crear un tema nuevo/ }))
    const form = screen.getByRole('form', { name: 'Crear un tema' })
    await waitFor(() => expect(within(form).getByRole('option', { name: 'Dudas de principiantes' })).toBeInTheDocument())
    await userEvent.type(within(form).getByLabelText(/^Título/), 'Mi primer cosplay')
    await userEvent.type(within(form).getByLabelText(/^Mensaje/), 'Hola comunidad, empiezo ahora.')
    await userEvent.click(within(form).getByRole('button', { name: 'Publicar tema' }))
    expect(await screen.findByRole('heading', { level: 1, name: 'Mi primer cosplay' })).toBeInTheDocument()
    const post = fetchMock.mock.calls.find(([u, o]) => u === '/api/foros/principiantes/temas' && o?.method === 'POST')
    expect(JSON.parse(post[1].body)).toEqual({ titulo: 'Mi primer cosplay', contenido: 'Hola comunidad, empiezo ahora.' })
  })
})

describe('Tema y desafío', () => {
  it('el tema muestra respuestas y permite responder', async () => {
    const fetchMock = apiComunidad(
      {
        '/api/temas/t1': {
          ...TEMA, contenido: 'Busco ideas.', foro: FOROS[0], imagen_url: null, imagen_alt: null, credito_fotografo: null, credito_cosplayer: null,
          oculto: false, respuestas: [{ id: 'r1', contenido: 'Elige uno que te guste.', autor: { id: 'u3', nombre: 'Rocío' }, created_at: TEMA.created_at }],
        },
        'POST /api/temas/t1/respuestas': { status: 201, cuerpo: { id: 'r2' } },
      },
      { usuario: USUARIO },
    )
    montar('/comunidad/temas/t1')
    expect(await screen.findByText('Elige uno que te guste.')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText(/Tu respuesta/), '¡Gracias!')
    await userEvent.click(screen.getByRole('button', { name: 'Responder' }))
    expect(await screen.findByText('Tu respuesta fue publicada.')).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([u, o]) => u === '/api/temas/t1/respuestas' && o?.method === 'POST')).toBe(true)
  })

  it('el desafío lista participaciones con créditos y pide sesión para participar', async () => {
    apiComunidad({ '/api/desafios/d1': { ...DESAFIO, lista_participaciones: [PARTICIPACION], ganador_participacion_id: null, ya_participo: false } })
    montar('/desafios/d1')
    expect(await screen.findByRole('heading', { level: 1, name: 'Reinterpreta un clásico' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Hechicera reciclada' })).toBeInTheDocument()
    expect(screen.getByText('Cosplay: @runa')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Inicia sesión para participar' })).toBeInTheDocument()
  })
})
