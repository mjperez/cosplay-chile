import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ADMIN, USUARIO, montar, simularApi } from './utilidades'

const PORTADA = {
  estadisticas: { personas: 12, guias: 17, proveedores: 13, tiendas: 8, comunidades: 8, eventos_proximos: 11, temas: 10, regiones_con_presencia: 9 },
  ultimas_guias: [
    { id: 'g1', titulo: 'Armadura en EVA', nivel: 'INTERMEDIO', categoria: { nombre: 'Confección' }, tipo: 'GUIA' },
  ],
  proximos_eventos: [
    { id: 'e1', nombre: 'Meetup de verano', fecha_inicio: '2026-12-05', tipo: 'MEETUP', comuna: 'Valparaíso', lugar: 'Parque', region: 'VA' },
  ],
  temas_destacados: [
    { id: 't1', titulo: '¿Qué personaje elegir?', foro_titulo: 'Novatos', respuestas: 3, created_at: new Date().toISOString() },
  ],
  trajes_recientes: [
    { id: 'p1', titulo: 'Hechicera', imagen_url: '/media/a.svg', imagen_alt: 'Cosplayer con sombrero', credito_cosplayer: '@runa', credito_fotografo: '@astra' },
  ],
  desafio_actual: null,
}

describe('Layout global', () => {
  it('muestra la navegación principal, el pie y las acciones de visitante', async () => {
    simularApi({ '/api/inicio': PORTADA })
    montar('/')
    const nav = screen.getByRole('navigation', { name: 'Principal' })
    for (const s of ['Guías', 'Directorio', 'Calendario', 'Comunidad']) {
      expect(within(nav).getByRole('link', { name: s })).toBeInTheDocument()
    }
    expect(screen.getAllByRole('link', { name: 'Registrarse' }).length).toBeGreaterThan(0)
    expect(screen.getByRole('link', { name: 'Saltar al contenido principal' })).toHaveAttribute('href', '#contenido')
    expect(screen.getByText(/Plataforma gratuita; no procesa pagos/)).toBeInTheDocument()
  })

  it('con sesión de moderación muestra la campana y el acceso al panel', async () => {
    simularApi({ '/api/inicio': PORTADA }, { usuario: ADMIN })
    montar('/')
    const boton = await screen.findByRole('button', { name: /Menú de mi cuenta/ })
    expect(screen.getByRole('button', { name: /Notificaciones/ })).toBeInTheDocument()
    await userEvent.click(boton)
    expect(screen.getAllByRole('link', { name: 'Panel de moderación' }).length).toBeGreaterThan(0)
  })

  it('el menú móvil se abre y cierra con su botón', async () => {
    simularApi({ '/api/inicio': PORTADA })
    montar('/')
    const boton = screen.getByRole('button', { name: 'Menú' })
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('navigation', { name: 'Principal (móvil)' })).toBeVisible()
  })
})

describe('Inicio', () => {
  it('muestra cifras, eventos, hilos, guías y trajes reales de /api/inicio', async () => {
    simularApi({ '/api/inicio': PORTADA })
    montar('/')
    expect(screen.getByRole('heading', { level: 1, name: /De la idea/ })).toBeInTheDocument()
    expect(await screen.findByText('21')).toBeInTheDocument() // 13 proveedores + 8 tiendas
    expect(screen.getByRole('link', { name: /Meetup de verano/ })).toHaveAttribute('href', '/calendario/e1')
    expect(screen.getByRole('link', { name: /¿Qué personaje elegir\?/ })).toHaveAttribute('href', '/comunidad/temas/t1')
    expect(screen.getByRole('link', { name: /Armadura en EVA/ })).toHaveAttribute('href', '/guias/g1')
    expect(screen.getByText('Cosplay: @runa · Foto: @astra')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Cosplayer con sombrero' })).toBeInTheDocument()
  })

  it('las tarjetas de rol llevan al registro con el tipo de perfil', async () => {
    simularApi({ '/api/inicio': PORTADA })
    montar('/')
    expect(screen.getByRole('link', { name: /^Tienda/ })).toHaveAttribute('href', '/registro?tipo=TIENDA')
    expect(screen.getByRole('link', { name: /^Visitante/ })).toHaveAttribute('href', '/guias')
  })

  it('con sesión, el llamado final invita a publicar en vez de registrarse', async () => {
    simularApi({ '/api/inicio': PORTADA }, { usuario: USUARIO })
    montar('/')
    expect(await screen.findByRole('heading', { name: 'Comparte lo que sabes' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Enviar un tutorial' })).toHaveAttribute('href', '/guias/publicar')
  })

  it('el filtro rápido por región lleva al directorio filtrado', async () => {
    simularApi({ '/api/inicio': PORTADA })
    montar('/')
    const filtro = await screen.findByLabelText('Filtrar por región')
    await waitFor(() => expect(within(filtro).getByRole('option', { name: 'Valparaíso' })).toBeInTheDocument())
    await userEvent.selectOptions(filtro, 'VA')
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('/directorio?region=VA')
  })

  it('el buscador de la portada ofrece sugerencias y busca con Enter', async () => {
    simularApi({
      '/api/inicio': PORTADA,
      '/api/busqueda/sugerencias': [{ tipo: 'guia', id: 'g1', titulo: 'Armadura en EVA', subtitulo: 'Confección', enlace: '/guias/g1' }],
    })
    montar('/')
    const caja = screen.getByRole('combobox', { name: /Buscar guías, profesionales/ })
    await userEvent.type(caja, 'eva')
    expect(await screen.findByRole('option', { name: /Armadura en EVA/ })).toBeInTheDocument()
    await userEvent.keyboard('{Enter}')
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('/buscar?q=eva')
  })
})

describe('Buscar', () => {
  it('agrupa los resultados por tipo', async () => {
    simularApi({
      '/api/busqueda': {
        total: 2,
        grupos: {
          guia: [{ id: 'g1', titulo: 'Armadura en EVA', subtitulo: 'Confección', enlace: '/guias/g1' }],
          tienda: [{ id: 'd1', titulo: 'Foam Factory', subtitulo: 'Valparaíso', enlace: '/directorio/d1' }],
        },
      },
    })
    montar('/buscar?q=eva')
    expect(await screen.findByRole('heading', { name: /Guías y tutoriales/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Foam Factory/ })).toHaveAttribute('href', '/directorio/d1')
    expect(screen.getByText('2 resultados')).toBeInTheDocument()
  })
})
