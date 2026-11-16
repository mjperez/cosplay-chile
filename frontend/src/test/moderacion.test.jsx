import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ADMIN, USUARIO, montar, simularApi } from './utilidades'

const PENDIENTE = {
  id: 'c1', tipo: 'GUIA', titulo: 'Guantes articulados en EVA', descripcion: 'Paso a paso.', nivel: 'INTERMEDIO', estado: 'PENDIENTE',
  categoria: { id: 'k1', slug: 'props-armaduras', nombre: 'Props y armaduras' }, autor: { id: 'u1', nombre: 'Camila' },
  created_at: new Date().toISOString(), pasos: ['Cortar', 'Pegar'], materiales: ['EVA'], imagen_url: null,
}
const REPORTE = {
  id: 'r1', tipo_objeto: 'RESPUESTA', objeto_id: 'x1', motivo: 'SPAM', detalle: 'Publicidad', estado: 'ABIERTO', resolucion: null,
  created_at: '2026-11-15T10:00:00Z', resuelto_at: null, reportante: { id: 'u1', nombre: 'Camila' }, objeto_texto: 'Compra seguidores aquí',
  objeto_enlace: '/comunidad/temas/t1#respuesta-x1', objeto_oculto: false, autor_objeto: { id: 'u9', nombre: 'Spammer' }, autor_objeto_estado: 'ACTIVO',
}
const hace = (dias) => new Date(Date.now() - dias * 86400000).toISOString()

function apiModeracion(extra = {}) {
  return simularApi(
    {
      '/api/moderacion/resumen': { contenidos_pendientes: 1, eventos_pendientes: 2, reportes_abiertos: 1, contactos_nuevos: 0 },
      '/api/moderacion/usuarios': (u) => (u.searchParams.get('estado') === 'SUSPENDIDO' ? [{ id: 's1' }, { id: 's2' }] : []),
      '/api/moderacion/reportes': (u) => {
        const e = u.searchParams.get('estado')
        if (e === 'RESUELTO') return [{ ...REPORTE, id: 'a', estado: 'RESUELTO', resuelto_at: hace(1) }, { ...REPORTE, id: 'b', estado: 'RESUELTO', resuelto_at: hace(20) }]
        if (e === 'DESCARTADO') return [{ ...REPORTE, id: 'c', estado: 'DESCARTADO', resuelto_at: hace(2) }]
        return [REPORTE]
      },
      '/api/moderacion/contenidos': [PENDIENTE],
      ...extra,
    },
    { usuario: ADMIN },
  )
}

describe('Panel de moderación', () => {
  it('una cuenta sin rol de moderación no puede entrar', async () => {
    simularApi({}, { usuario: USUARIO })
    montar('/moderacion')
    expect(await screen.findByText('Esta sección es solo para el equipo de moderación.')).toBeInTheDocument()
  })

  it('muestra los contadores, incluidos los calculados con los listados', async () => {
    apiModeracion()
    montar('/moderacion')
    const resumen = await screen.findByLabelText('Resumen')
    await waitFor(() => expect(within(resumen).getByText('Pendientes de revisión').previousSibling).toHaveTextContent('3'))
    expect(within(resumen).getByText('Cuentas suspendidas').previousSibling).toHaveTextContent('2')
    expect(within(resumen).getByText('Reportes resueltos esta semana').previousSibling).toHaveTextContent('2')
  })

  it('aprueba y publica un tutorial pendiente (UC6)', async () => {
    const fetchMock = apiModeracion({ 'POST /api/moderacion/contenidos/c1/publicar': { ...PENDIENTE, estado: 'PUBLICADO' } })
    montar('/moderacion')
    expect(await screen.findByRole('heading', { level: 3, name: 'Guantes articulados en EVA' })).toBeInTheDocument()
    expect(screen.getByText('2 pasos · 1 materiales · Sin imágenes adjuntas')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /Aprobar y publicar/ }))
    expect(await screen.findByText(/Publicaste «Guantes articulados en EVA»/)).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([u, o]) => u === '/api/moderacion/contenidos/c1/publicar' && o?.method === 'POST')).toBe(true)
  })

  it('las secciones se recorren con flechas y resuelve un reporte con «Ocultar y suspender»', async () => {
    const fetchMock = apiModeracion({ 'POST /api/moderacion/reportes/r1/resolver': { ...REPORTE, estado: 'RESUELTO' } })
    montar('/moderacion')
    const primera = await screen.findByRole('tab', { name: /Tutoriales pendientes/ })
    primera.focus()
    await userEvent.keyboard('{ArrowDown}')
    expect(screen.getByRole('tab', { name: /Reportes de contenido/ })).toHaveAttribute('aria-selected', 'true')
    expect(await screen.findByText('Compra seguidores aquí')).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText('Acción'), 'OCULTAR_Y_SUSPENDER')
    await userEvent.type(screen.getByLabelText(/Resolución/), 'Spam reiterado')
    await userEvent.click(screen.getByRole('button', { name: /Aplicar/ }))
    expect(await screen.findByText('Reporte resuelto y registrado en la bitácora.')).toBeInTheDocument()
    const post = fetchMock.mock.calls.find(([u]) => u === '/api/moderacion/reportes/r1/resolver')
    expect(JSON.parse(post[1].body)).toEqual({ accion: 'OCULTAR_Y_SUSPENDER', resolucion: 'Spam reiterado' })
  })
})
