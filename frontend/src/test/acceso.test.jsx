import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { USUARIO, montar, simularApi } from './utilidades'

const TOKEN = { access_token: 'nuevo-token', token_type: 'bearer', expira_en: 3600, usuario: USUARIO }

describe('Acceso (UC-01)', () => {
  it('inicia sesión y vuelve a la página pedida', async () => {
    const fetchMock = simularApi({ 'POST /api/auth/login': TOKEN, '/api/contenidos': { items: [], total: 0, pagina: 1, por_pagina: 12, paginas: 0 } })
    montar('/ingresar?siguiente=%2Fguias')
    expect(screen.getByRole('tab', { name: 'Iniciar sesión' })).toHaveAttribute('aria-selected', 'true')
    await userEvent.type(screen.getByLabelText(/Correo electrónico/), 'camila@demo.cl')
    await userEvent.type(screen.getByLabelText(/^Contraseña/), 'Cosplay2026!')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    await waitFor(() => expect(screen.getByTestId('ubicacion')).toHaveTextContent(/^\/guias$/))
    const post = fetchMock.mock.calls.find(([u]) => u === '/api/auth/login')
    expect(JSON.parse(post[1].body)).toEqual({ email: 'camila@demo.cl', password: 'Cosplay2026!' })
    expect(localStorage.getItem('cosplaychile.token')).toBe('nuevo-token')
  })

  it('muestra «Datos incorrectos» con credenciales erróneas', async () => {
    simularApi({ 'POST /api/auth/login': { status: 401, cuerpo: { detail: 'Datos incorrectos' } } })
    montar('/ingresar')
    await userEvent.type(screen.getByLabelText(/Correo electrónico/), 'x@demo.cl')
    await userEvent.type(screen.getByLabelText(/^Contraseña/), 'mala')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Datos incorrectos')
  })

  it('una cuenta suspendida recibe el enlace al formulario de contacto', async () => {
    simularApi({
      'POST /api/auth/login': { status: 403, cuerpo: { detail: { mensaje: 'Tu cuenta está suspendida.', codigo: 'CUENTA_SUSPENDIDA' } } },
    })
    montar('/ingresar')
    await userEvent.type(screen.getByLabelText(/Correo electrónico/), 'suspendido@demo.cl')
    await userEvent.type(screen.getByLabelText(/^Contraseña/), 'Cosplay2026!')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByText('Tu cuenta está suspendida.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /formulario de contacto/ })).toHaveAttribute('href', '/contacto?tipo=CUENTA')
  })

  it('las pestañas cambian entre /ingresar y /registro', async () => {
    simularApi({})
    montar('/ingresar')
    await userEvent.click(screen.getByRole('tab', { name: 'Crear cuenta' }))
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('/registro')
    expect(screen.getByRole('form', { name: 'Crear cuenta' })).toBeInTheDocument()
  })

  it('el registro envía tipo de perfil, opt-in al directorio y consentimiento (RF-10, RNF-11)', async () => {
    const fetchMock = simularApi({ 'POST /api/auth/registro': { status: 201, cuerpo: TOKEN }, '/api/directorio/mi-ficha': { status: 404, cuerpo: { detail: 'Sin ficha' } } })
    montar('/registro?tipo=TIENDA')
    const form = screen.getByRole('form', { name: 'Crear cuenta' })
    expect(within(form).getByRole('button', { name: 'Tienda' })).toHaveAttribute('aria-pressed', 'true')
    expect(within(form).getByText('Registro para proveedores y tiendas')).toBeInTheDocument()
    await userEvent.type(within(form).getByLabelText(/Nombre o alias/), 'Telas del Sur')
    await userEvent.type(within(form).getByLabelText(/Correo electrónico/), 'telas@demo.cl')
    await userEvent.type(within(form).getByLabelText(/^Contraseña/), 'Clave2026segura')
    const interruptor = within(form).getByRole('switch', { name: /Visibilizar mi perfil/ })
    await userEvent.click(interruptor)
    expect(interruptor).toHaveAttribute('aria-checked', 'true')
    await userEvent.click(within(form).getByRole('checkbox', { name: /Acepto el tratamiento/ }))
    await userEvent.click(within(form).getByRole('button', { name: 'Crear cuenta' }))
    await waitFor(() => expect(screen.getByTestId('ubicacion')).toHaveTextContent('/perfil?bienvenida=1'))
    const post = fetchMock.mock.calls.find(([u]) => u === '/api/auth/registro')
    expect(JSON.parse(post[1].body)).toEqual({
      nombre: 'Telas del Sur', email: 'telas@demo.cl', password: 'Clave2026segura', tipo_perfil: 'TIENDA', region: null, perfil_publico: true, acepta_privacidad: true,
    })
  })

  it('recuperar contraseña muestra la respuesta del servidor', async () => {
    simularApi({ 'POST /api/auth/recuperar': { status: 202, cuerpo: { mensaje: 'Si el correo existe, te enviamos un enlace.' } } })
    montar('/recuperar')
    await userEvent.type(screen.getByLabelText(/Correo electrónico/), 'camila@demo.cl')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar enlace' }))
    expect(await screen.findByText('Si el correo existe, te enviamos un enlace.')).toBeInTheDocument()
  })
})

describe('Perfil (UC4)', () => {
  const FAVS = [
    { id: 'f1', tipo: 'CONTENIDO', objeto_id: 'g1', titulo: 'Armadura en EVA', subtitulo: 'Props', enlace: '/guias/g1' },
    { id: 'f2', tipo: 'EVENTO', objeto_id: 'e1', titulo: 'Meetup de verano', subtitulo: '05-12-2026', enlace: '/calendario/e1' },
  ]
  function apiPerfil(extra = {}) {
    return simularApi(
      {
        '/api/favoritos': FAVS,
        '/api/contenidos/mios': [{ id: 'c1', titulo: 'Mi tutorial', estado: 'PENDIENTE', created_at: '2026-11-10T10:00:00Z' }],
        '/api/directorio/mi-ficha': { status: 404, cuerpo: { detail: 'Sin ficha' } },
        ...extra,
      },
      { usuario: USUARIO },
    )
  }

  it('guarda los cambios del perfil', async () => {
    const fetchMock = apiPerfil({ 'PUT /api/perfil': { ...USUARIO, perfil: { ...USUARIO.perfil, biografia: 'Hago cosplay desde 2020.' } } })
    montar('/perfil')
    await userEvent.type(await screen.findByLabelText(/Biografía/), 'Hago cosplay desde 2020.')
    await userEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    expect(await screen.findByText('Tus cambios fueron guardados.')).toBeInTheDocument()
    const put = fetchMock.mock.calls.find(([u, o]) => u === '/api/perfil' && o?.method === 'PUT')
    expect(JSON.parse(put[1].body)).toMatchObject({ biografia: 'Hago cosplay desde 2020.', region: 'RM' })
  })

  it('muestra favoritos por pestaña y los envíos con su estado', async () => {
    apiPerfil()
    montar('/perfil')
    expect(await screen.findByRole('link', { name: 'Armadura en EVA' })).toBeInTheDocument()
    const grupo = screen.getByRole('group', { name: 'Tipo' })
    await userEvent.click(within(grupo).getByRole('button', { name: 'Eventos' }))
    expect(screen.getByRole('link', { name: 'Meetup de verano' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Armadura en EVA' })).not.toBeInTheDocument()
    expect(await screen.findByText('Mi tutorial')).toBeInTheDocument()
  })

  it('eliminar la cuenta exige escribir ELIMINAR', async () => {
    apiPerfil({ 'DELETE /api/perfil': { mensaje: 'Cuenta eliminada' }, '/api/inicio': { estadisticas: null } })
    montar('/perfil')
    const boton = await screen.findByRole('button', { name: 'Eliminar mi cuenta definitivamente' })
    expect(boton).toBeDisabled()
    await userEvent.type(screen.getByLabelText(/Para confirmar escribe/), 'ELIMINAR')
    expect(boton).toBeEnabled()
    await userEvent.click(boton)
    await waitFor(() => expect(screen.getByTestId('ubicacion')).toHaveTextContent('/?cuenta=eliminada'))
  })

  it('cerrar sesión desde una página protegida lleva a la portada, no a /ingresar', async () => {
    apiPerfil({ '/api/inicio': { estadisticas: null } })
    montar('/perfil')
    await userEvent.click(await screen.findByRole('button', { name: /Menú de mi cuenta/ }))
    await userEvent.click(screen.getAllByRole('button', { name: 'Cerrar sesión' })[0])
    await waitFor(() => expect(screen.getByTestId('ubicacion')).toHaveTextContent(/^\/$/))
    expect(localStorage.getItem('cosplaychile.token')).toBeNull()
  })
})
