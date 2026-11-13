/**
 * Módulos de comunidad: calendario, foro, desafíos, perfiles y directorio
 * de tiendas/grupos.
 *
 * El cliente es independiente de `api.ts` a propósito: así los módulos nuevos
 * no tocan el cliente ya probado, pero comparten `ErrorApi` y la clave del
 * token para que las páginas manejen los errores siempre igual.
 *
 * Todas las rutas que recibe `peticionModulo` van completas, con el prefijo
 * `/api/v1`, igual que en `api.ts`.
 */

import { CLAVE_TOKEN, ErrorApi } from './api'

/* ==========================================================================
   Tipos del contrato (copiados tal cual)
   ========================================================================== */

export interface Evento {
  id_evento: string
  nombre: string
  tipo: 'convencion' | 'concurso' | 'feria' | 'taller' | 'otro'
  fecha_inicio: string
  fecha_fin: string | null
  lugar: string
  region: string | null
  enlace_oficial: string | null
  total_participantes: number
  creado_en: string
}
export interface PaginaEventos { total: number; limite: number; desplazamiento: number; elementos: Evento[] }
export interface Participacion {
  id_participacion: string
  id_usuario: string
  id_evento: string
  personaje: string | null
  nombre_usuario: string
}
export interface PaginaParticipaciones { total: number; elementos: Participacion[] }

export interface Tema {
  id_tema: string
  /** Permite decidir en el cliente si el usuario puede cerrar el tema. */
  id_creador: string
  titulo: string
  categoria: string
  contenido: string | null
  estado: 'abierto' | 'cerrado' | 'oculto'
  nombre_autor: string
  total_respuestas: number
  creado_en: string
}
export interface PaginaTemas { total: number; limite: number; desplazamiento: number; elementos: Tema[] }
export interface Respuesta {
  id_respuesta: string
  id_tema: string
  contenido: string
  nombre_autor: string
  creado_en: string
}
export interface TemaDetalle extends Tema { respuestas: Respuesta[] }
export interface DatosTema { titulo: string; categoria: string; contenido: string }

export interface Desafio {
  id_desafio: string
  titulo: string
  mes: string
  id_ganador: string | null
  nombre_ganador: string | null
  creado_en: string
}
export interface PaginaDesafios { total: number; elementos: Desafio[] }

export interface Perfil {
  id_usuario: string
  nombre: string
  rol: string
  region: string
  especialidad: string | null
  portafolio_url: string | null
  biografia: string | null
}
export interface DatosPerfil {
  especialidad?: string | null
  portafolio_url?: string | null
  biografia?: string | null
  region?: string | null
}

export interface Tienda {
  id_tienda: string
  nombre: string
  tipo: 'telas' | 'insumos' | 'pelucas' | 'impresion_3d' | 'otro'
  envia_a_chile: boolean
  enlace_web: string | null
  region: string | null
}
export interface Grupo {
  id_comunidad: string
  nombre: string
  region: string | null
  plataforma: 'facebook' | 'discord' | 'instagram' | 'whatsapp' | 'foro' | 'otro'
  enlace: string | null
}
export interface PaginaTiendas { total: number; elementos: Tienda[] }
export interface PaginaGrupos { total: number; elementos: Grupo[] }

/* ==========================================================================
   Tipos auxiliares de entrada.
   El contrato solo fija los tipos de salida y `DatosTema` / `DatosPerfil`;
   estos describen los body y query de la tabla de endpoints.
   Se declaran como `type` (no `interface`) para poder pasarlos al constructor
   de consultas, que espera un registro indexado por string.
   ========================================================================== */

export type FiltrosEventos = {
  tipo?: string
  region?: string
  q?: string
  limite?: number
  desplazamiento?: number
}
export type FiltrosTemas = {
  categoria?: string
  q?: string
  limite?: number
  desplazamiento?: number
}
export type FiltrosTiendas = {
  tipo?: string
  region?: string
  q?: string
  limite?: number
  desplazamiento?: number
}
export type FiltrosGrupos = {
  region?: string
  plataforma?: string
  limite?: number
  desplazamiento?: number
}

/** Respuesta de `/eventos/mis`: el contrato la describe pero no le da nombre. */
export interface ListaEventos { total: number; elementos: Evento[] }

export interface DatosEvento {
  nombre: string
  tipo: Evento['tipo']
  fecha_inicio: string
  fecha_fin?: string | null
  lugar: string
  region?: string | null
  enlace_oficial?: string | null
}

export interface DatosDesafio { titulo: string; mes: string }

/* ==========================================================================
   Cliente HTTP
   ========================================================================== */

const BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')

type ParametrosConsulta = Record<string, string | number | null | undefined>

/** Arma `?clave=valor`, omitiendo vacíos. No codifica dos veces una query ya hecha. */
function aConsulta(parametros: ParametrosConsulta): string {
  const busqueda = new URLSearchParams()
  for (const [clave, valor] of Object.entries(parametros)) {
    if (valor === null || valor === undefined || valor === '') continue
    busqueda.set(clave, String(valor))
  }
  return busqueda.toString()
}

/**
 * Los listados aceptan un objeto de filtros o la cadena de query ya armada.
 * La cadena sirve de clave estable del `useEffect` en las páginas, igual que
 * `api.proveedores(consulta)` en el directorio.
 */
function resolverConsulta(filtros: ParametrosConsulta | string): string {
  const texto =
    typeof filtros === 'string' ? filtros.replace(/^\?/, '') : aConsulta(filtros)
  return texto ? `?${texto}` : ''
}

/** FastAPI devuelve `detail` como texto en los 4xx y como lista en los 422. */
function mensajeDeError(cuerpo: unknown, estado: number): string {
  if (cuerpo && typeof cuerpo === 'object' && 'detail' in cuerpo) {
    const detalle = (cuerpo as { detail: unknown }).detail
    if (typeof detalle === 'string') return detalle
    if (Array.isArray(detalle)) {
      const partes = detalle
        .map((item) => (item as { msg?: string }).msg ?? '')
        .filter(Boolean)
      if (partes.length > 0) return partes.join('. ')
    }
  }
  return `Error ${estado}`
}

/**
 * Petición a los módulos nuevos. Añade el token de `localStorage`, el
 * `Content-Type` cuando hay body y convierte cualquier 4xx/5xx en `ErrorApi`
 * con el mensaje `detail` del backend. Un 204 devuelve `null` (cuerpo vacío).
 */
export async function peticionModulo<T>(
  ruta: string,
  opciones: RequestInit = {},
): Promise<T> {
  const cabeceras = new Headers(opciones.headers)
  if (opciones.body && !cabeceras.has('Content-Type')) {
    cabeceras.set('Content-Type', 'application/json')
  }
  const token = localStorage.getItem(CLAVE_TOKEN)
  if (token) cabeceras.set('Authorization', `Bearer ${token}`)

  const respuesta = await fetch(`${BASE}${ruta}`, { ...opciones, headers: cabeceras })
  const texto = await respuesta.text()
  let cuerpo: unknown = null
  if (texto) {
    try {
      cuerpo = JSON.parse(texto)
    } catch {
      cuerpo = null
    }
  }

  if (!respuesta.ok) {
    throw new ErrorApi(respuesta.status, mensajeDeError(cuerpo, respuesta.status))
  }
  return cuerpo as T
}

function rutaConId(prefijo: string, id: string): string {
  return `${prefijo}/${encodeURIComponent(id)}`
}

export const modulosApi = {
  // --- Eventos ---------------------------------------------------------
  eventos: (filtros: FiltrosEventos | string = {}) =>
    peticionModulo<PaginaEventos>(`/api/v1/eventos${resolverConsulta(filtros)}`),

  misEventos: () => peticionModulo<ListaEventos>('/api/v1/eventos/mis'),

  evento: (id: string) => peticionModulo<Evento>(rutaConId('/api/v1/eventos', id)),

  participaciones: (id: string) =>
    peticionModulo<PaginaParticipaciones>(
      `${rutaConId('/api/v1/eventos', id)}/participaciones`,
    ),

  crearEvento: (datos: DatosEvento) =>
    peticionModulo<Evento>('/api/v1/eventos', {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  participar: (id: string, personaje?: string) =>
    peticionModulo<Participacion>(`${rutaConId('/api/v1/eventos', id)}/participar`, {
      method: 'POST',
      body: JSON.stringify({ personaje }),
    }),

  cancelarParticipacion: (id: string) =>
    peticionModulo<void>(`${rutaConId('/api/v1/eventos', id)}/participar`, {
      method: 'DELETE',
    }),

  // --- Foro ------------------------------------------------------------
  temas: (filtros: FiltrosTemas | string = {}) =>
    peticionModulo<PaginaTemas>(`/api/v1/foro/temas${resolverConsulta(filtros)}`),

  tema: (id: string) =>
    peticionModulo<TemaDetalle>(rutaConId('/api/v1/foro/temas', id)),

  crearTema: (datos: DatosTema) =>
    peticionModulo<Tema>('/api/v1/foro/temas', {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  responderTema: (id: string, contenido: string) =>
    peticionModulo<Respuesta>(`${rutaConId('/api/v1/foro/temas', id)}/respuestas`, {
      method: 'POST',
      body: JSON.stringify({ contenido }),
    }),

  cerrarTema: (id: string) =>
    peticionModulo<Tema>(`${rutaConId('/api/v1/foro/temas', id)}/cerrar`, {
      method: 'POST',
    }),

  // --- Desafíos --------------------------------------------------------
  desafios: () => peticionModulo<PaginaDesafios>('/api/v1/desafios'),

  desafioVigente: () =>
    peticionModulo<Desafio | null>('/api/v1/desafios/vigente'),

  crearDesafio: (datos: DatosDesafio) =>
    peticionModulo<Desafio>('/api/v1/desafios', {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  asignarGanador: (id: string, id_usuario: string) =>
    peticionModulo<Desafio>(`${rutaConId('/api/v1/desafios', id)}/ganador`, {
      method: 'POST',
      body: JSON.stringify({ id_usuario }),
    }),

  // --- Perfiles --------------------------------------------------------
  perfilPropio: () => peticionModulo<Perfil>('/api/v1/perfiles/mio'),

  actualizarPerfil: (datos: DatosPerfil) =>
    peticionModulo<Perfil>('/api/v1/perfiles/mio', {
      method: 'PUT',
      body: JSON.stringify(datos),
    }),

  perfilPorId: (id_usuario: string) =>
    peticionModulo<Perfil>(rutaConId('/api/v1/perfiles', id_usuario)),

  // --- Comunidad -------------------------------------------------------
  tiendas: (filtros: FiltrosTiendas | string = {}) =>
    peticionModulo<PaginaTiendas>(`/api/v1/tiendas${resolverConsulta(filtros)}`),

  grupos: (filtros: FiltrosGrupos | string = {}) =>
    peticionModulo<PaginaGrupos>(`/api/v1/grupos${resolverConsulta(filtros)}`),
}

/* ==========================================================================
   Utilidades de presentación compartidas por las siete páginas
   ========================================================================== */

/** Mensaje uniforme para los catch: el detalle del backend o un texto claro. */
export function mensajeDeFallo(fallo: unknown, porDefecto: string): string {
  return fallo instanceof ErrorApi ? fallo.message : porDefecto
}

/**
 * El backend guarda los datetime como UTC "naive" (sin `Z`). Si el navegador
 * los leyera directo los tomaría como hora local y mostraría otra hora.
 * Solo se agrega `Z` a los valores fecha+hora que no traen zona explícita.
 */
export function aFecha(valor: string | null | undefined): Date | null {
  if (!valor) return null
  const tieneZona = /([zZ]|[+-]\d{2}:?\d{2})$/.test(valor)
  const texto = valor.includes('T') && !tieneZona ? `${valor}Z` : valor
  const fecha = new Date(texto)
  return Number.isNaN(fecha.getTime()) ? null : fecha
}

const ZONA_CHILE = 'America/Santiago'

export function formatearFecha(valor: string | null | undefined): string {
  const fecha = aFecha(valor)
  if (!fecha) return 'Fecha por confirmar'
  return new Intl.DateTimeFormat('es-CL', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: ZONA_CHILE,
  }).format(fecha)
}

export function formatearFechaHora(valor: string | null | undefined): string {
  const fecha = aFecha(valor)
  if (!fecha) return 'Fecha por confirmar'
  return new Intl.DateTimeFormat('es-CL', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: ZONA_CHILE,
  }).format(fecha)
}

/** `2026-11` -> `Noviembre de 2026`. Si el mes no es válido, se devuelve tal cual. */
export function formatearMes(mes: string): string {
  const [anio, numero] = mes.split('-')
  const fecha = new Date(Date.UTC(Number(anio), Number(numero) - 1, 1))
  if (Number.isNaN(fecha.getTime())) return mes
  const texto = new Intl.DateTimeFormat('es-CL', {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(fecha)
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

/** Solo se abre un enlace externo si es http(s): evita `javascript:` en el href. */
export function enlaceExterno(valor: string | null | undefined): string | null {
  if (!valor) return null
  return /^https?:\/\//i.test(valor.trim()) ? valor.trim() : null
}

export const REGIONES_CHILE = [
  'Arica y Parinacota',
  'Tarapacá',
  'Antofagasta',
  'Atacama',
  'Coquimbo',
  'Valparaíso',
  'Metropolitana',
  "O'Higgins",
  'Maule',
  'Ñuble',
  'Biobío',
  'La Araucanía',
  'Los Ríos',
  'Los Lagos',
  'Aysén',
  'Magallanes',
]

export const TIPOS_EVENTO: Evento['tipo'][] = [
  'convencion',
  'concurso',
  'feria',
  'taller',
  'otro',
]

export const ETIQUETAS_TIPO_EVENTO: Record<Evento['tipo'], string> = {
  convencion: 'Convención',
  concurso: 'Concurso',
  feria: 'Feria',
  taller: 'Taller',
  otro: 'Otro',
}

export const TONO_TIPO_EVENTO: Record<Evento['tipo'], 'marca' | 'acento' | 'neutro' | 'exito'> = {
  convencion: 'marca',
  concurso: 'acento',
  feria: 'exito',
  taller: 'neutro',
  otro: 'neutro',
}

/** Categorías declaradas en el backend; el foro además acepta categorías libres. */
export const CATEGORIAS_FORO = [
  'Armaduras y props',
  'Pelucas y maquillaje',
  'Costura y vestuario',
  'Presupuesto y compras',
  'Eventos y comunidad',
]

export const TIPOS_TIENDA: Tienda['tipo'][] = [
  'telas',
  'insumos',
  'pelucas',
  'impresion_3d',
  'otro',
]

export const ETIQUETAS_TIPO_TIENDA: Record<Tienda['tipo'], string> = {
  telas: 'Telas',
  insumos: 'Insumos',
  pelucas: 'Pelucas',
  impresion_3d: 'Impresión 3D',
  otro: 'Otro',
}

export const PLATAFORMAS: Grupo['plataforma'][] = [
  'facebook',
  'discord',
  'instagram',
  'whatsapp',
  'foro',
  'otro',
]

export const ETIQUETAS_PLATAFORMA: Record<Grupo['plataforma'], string> = {
  facebook: 'Facebook',
  discord: 'Discord',
  instagram: 'Instagram',
  whatsapp: 'WhatsApp',
  foro: 'Foro',
  otro: 'Otro',
}
