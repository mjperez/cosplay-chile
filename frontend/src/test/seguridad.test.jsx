import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { analizarEnlace } from '../pages/seguridad/enlaceReportable'
import { USUARIO, montar, simularApi } from './utilidades'

const ID = '3207a3cd-f3a7-4668-95e3-5920ebd947b3'
const ID2 = '1d047bbd-7c5a-48c5-8492-05d6d9a29c75'
const ORIGEN = 'http://localhost:5173'

describe('analizarEnlace', () => {
  it('reconoce guías, temas, respuestas, eventos y fichas del sitio', () => {
    expect(analizarEnlace(`${ORIGEN}/guias/${ID}`, ORIGEN)).toMatchObject({ tipo_objeto: 'CONTENIDO', objeto_id: ID })
    expect(analizarEnlace(`/comunidad/temas/${ID}`, ORIGEN)).toMatchObject({ tipo_objeto: 'TEMA', objeto_id: ID })
    expect(analizarEnlace(`${ORIGEN}/comunidad/temas/${ID}#respuesta-${ID2}`, ORIGEN)).toMatchObject({ tipo_objeto: 'RESPUESTA', objeto_id: ID2 })
    expect(analizarEnlace(`${ORIGEN}/calendario/${ID}/`, ORIGEN)).toMatchObject({ tipo_objeto: 'EVENTO' })
    expect(analizarEnlace(`${ORIGEN}/directorio/${ID.toUpperCase()}`, ORIGEN)).toMatchObject({ tipo_objeto: 'DIRECTORIO', objeto_id: ID })
  })

  it('rechaza enlaces externos o que no son contenido reportable', () => {
    expect(analizarEnlace(`https://otro.example/guias/${ID}`, ORIGEN)).toBeNull()
    expect(analizarEnlace(`${ORIGEN}/guias`, ORIGEN)).toBeNull()
    expect(analizarEnlace('texto cualquiera', ORIGEN)).toBeNull()
    expect(analizarEnlace('', ORIGEN)).toBeNull()
  })
})

describe('Seguridad y contacto', () => {
  it('visitante ve el acceso para reportar, el bloque de urgencias y los consejos', () => {
    simularApi({})
    montar('/seguridad')
    expect(screen.getByRole('tab', { name: 'Reportar contenido' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('link', { name: 'Ingresar para reportar' })).toBeInTheDocument()
    expect(screen.getByText('Carabineros (133)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Traslado seguro/ })).toBeInTheDocument()
  })

  it('con sesión reporta a partir de un enlace interno (RF-38)', async () => {
    const fetchMock = simularApi({ 'POST /api/reportes': { status: 201, cuerpo: { mensaje: 'Gracias por avisar.' } } }, { usuario: USUARIO })
    montar('/seguridad')
    const enlace = await screen.findByLabelText(/Enlace al contenido/)
    await userEvent.type(enlace, `${window.location.origin}/comunidad/temas/${ID}`)
    expect(screen.getByText('Detectamos: Tema del foro.')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText(/^Detalle/), 'Spam repetido')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar reporte' }))
    expect(await screen.findByRole('heading', { name: 'Recibimos tu mensaje' })).toBeInTheDocument()
    const post = fetchMock.mock.calls.find(([u]) => u === '/api/reportes')
    expect(JSON.parse(post[1].body)).toEqual({ tipo_objeto: 'TEMA', objeto_id: ID, motivo: 'INAPROPIADO', detalle: 'Spam repetido' })
  })

  it('no envía un reporte con un enlace no reconocido', async () => {
    const fetchMock = simularApi({}, { usuario: USUARIO })
    montar('/seguridad')
    await userEvent.type(await screen.findByLabelText(/Enlace al contenido/), 'https://otro.example/algo')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar reporte' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Pega el enlace de una guía')
    expect(fetchMock.mock.calls.some(([u]) => u === '/api/reportes')).toBe(false)
  })

  it('/contacto?tipo=CUENTA abre el contacto con el motivo de cuenta y exige autorización (RF-40)', async () => {
    const fetchMock = simularApi({ 'POST /api/contacto': { status: 201, cuerpo: { mensaje: 'Recibimos tu mensaje.' } } })
    montar('/contacto?tipo=CUENTA')
    expect(screen.getByRole('tab', { name: 'Contacto y denuncias' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByLabelText(/^Asunto/)).toHaveValue('Mi cuenta aparece suspendida')
    await userEvent.type(screen.getByLabelText(/^Nombre/), 'Cuenta Suspendida')
    await userEvent.type(screen.getByLabelText(/Correo para responderte/), 'suspendido@demo.cl')
    await userEvent.type(screen.getByLabelText(/^Mensaje/), 'Creo que es un error, por favor revisen.')
    await userEvent.click(screen.getByRole('button', { name: 'Enviar mensaje' }))
    expect(screen.getByRole('alert')).toHaveTextContent('necesitamos tu autorización')
    await userEvent.click(screen.getByRole('checkbox', { name: /Autorizo el uso de mis datos/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Enviar mensaje' }))
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Recibimos tu mensaje' })).toBeInTheDocument())
    const post = fetchMock.mock.calls.find(([u]) => u === '/api/contacto')
    expect(JSON.parse(post[1].body)).toMatchObject({ tipo: 'CUENTA', email: 'suspendido@demo.cl', asunto: 'Mi cuenta aparece suspendida' })
  })
})
