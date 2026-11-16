import { render } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { vi } from 'vitest'
import App from '../App'
import { AuthProvider } from '../contexto/AuthContext'
import { MetaProvider } from '../contexto/MetaContext'

export const META = {
  regiones: { RM: 'Metropolitana de Santiago', VA: 'Valparaíso', BI: 'Biobío' },
  niveles: { PRINCIPIANTE: 'Principiante', INTERMEDIO: 'Intermedio', AVANZADO: 'Avanzado' },
  especialidades: { SASTRERIA: 'Sastrería', MAQUILLAJE: 'Maquillaje', FOTOGRAFIA: 'Fotografía' },
  tipos_producto: { TELAS: 'Telas', TERMOPLASTICOS: 'Termoplásticos' },
  tipos_evento: { CONVENCION: 'Convención', CONCURSO: 'Concurso', MEETUP: 'Meetup', TALLER: 'Taller' },
  tipos_perfil: { COSPLAYER: 'Cosplayer', COSMAKER: 'Cosmaker', TIENDA: 'Tienda', ORGANIZADOR: 'Organizador' },
  tipos_contenido: { GUIA: 'Guía / tutorial', ENTREVISTA: 'Entrevista', ARTICULO: 'Artículo técnico' },
  motivos_reporte: { SPAM: 'Spam', ACOSO: 'Acoso', OTRO: 'Otro' },
  tipos_contacto: { DUDA: 'Duda', SUGERENCIA: 'Sugerencia', DENUNCIA: 'Denuncia', CUENTA: 'Problema con mi cuenta' },
}

export const USUARIO = {
  id: 'u1',
  nombre: 'Camila',
  email: 'camila@demo.cl',
  rol: 'USUARIO',
  estado: 'ACTIVO',
  perfil: { tipo_perfil: 'COSPLAYER', region: 'RM', redes_sociales: [], portafolio: [], perfil_publico: false },
}
export const ADMIN = { ...USUARIO, id: 'a1', nombre: 'Moderación', email: 'admin@cosplaychile.cl', rol: 'ADMIN' }

function respuesta(status, cuerpo) {
  return Promise.resolve(
    new Response(JSON.stringify(cuerpo), { status, headers: { 'Content-Type': 'application/json' } }),
  )
}

/**
 * Simula la API: `rutas` asocia "MÉTODO /ruta" o "/ruta" (sin query) a un objeto o a una función
 * (url, opciones) => objeto | {status, cuerpo}. Lo no declarado responde 404.
 * Devuelve el mock de fetch para revisar las llamadas.
 */
export function simularApi(rutas = {}, { usuario } = {}) {
  const tabla = {
    '/api/meta': META,
    '/api/categorias': [],
    '/api/notificaciones': { no_leidas: 0, items: [] },
    ...(usuario ? { '/api/auth/me': usuario } : {}),
    ...rutas,
  }
  if (usuario) localStorage.setItem('cosplaychile.token', 'token-de-prueba')
  const fetchMock = vi.fn((url, opciones = {}) => {
    const u = new URL(url, 'http://localhost')
    const metodo = (opciones.method || 'GET').toUpperCase()
    const valor = tabla[`${metodo} ${u.pathname}`] ?? (metodo === 'GET' ? tabla[u.pathname] : undefined)
    if (valor === undefined) return respuesta(404, { detail: 'No encontrado' })
    const r = typeof valor === 'function' ? valor(u, opciones) : valor
    if (r && typeof r === 'object' && 'status' in r && 'cuerpo' in r) return respuesta(r.status, r.cuerpo)
    return respuesta(200, r)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

export function UbicacionActual() {
  const l = useLocation()
  return <output data-testid="ubicacion">{l.pathname + l.search}</output>
}

// Monta la aplicación completa (rutas, layout y contextos) en la ruta indicada
export function montar(ruta = '/') {
  return render(
    <MemoryRouter initialEntries={[ruta]}>
      <MetaProvider>
        <AuthProvider>
          <App />
          <UbicacionActual />
        </AuthProvider>
      </MetaProvider>
    </MemoryRouter>,
  )
}
