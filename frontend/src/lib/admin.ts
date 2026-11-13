/**
 * Cliente del panel de administración.
 *
 * Reutiliza `peticionModulo` para no duplicar el manejo de token, errores y
 * URL base. Todas las rutas cuelgan de `/api/v1/admin`, que en el backend
 * tiene la dependencia de rol en el router: si se agrega un endpoint allá,
 * nace protegido sin que este archivo tenga que recordarlo.
 */

import type { Categoria, Contenido, PaginaContenido, Usuario } from './api'
import {
  peticionModulo,
  type DatosDesafio,
  type DatosEvento,
  type Desafio,
  type Evento,
  type Grupo,
  type PaginaDesafios,
  type PaginaEventos,
  type PaginaGrupos,
  type PaginaTemas,
  type PaginaTiendas,
  type Tema,
  type Tienda,
} from './modulos'

const RAIZ = '/api/v1/admin'

export interface ResumenAdmin {
  usuarios: number
  usuarios_activos: number
  contenido_pendiente: number
  contenido_publicado: number
  contenido_rechazado: number
  eventos: number
  inscripciones: number
  temas: number
  temas_abiertos: number
  respuestas: number
  desafios: number
  tiendas: number
  grupos: number
  proveedores: number
  categorias: number
  generado_en: string
}

export interface PaginaUsuariosAdmin {
  total: number
  limite: number
  desplazamiento: number
  elementos: Usuario[]
}

export type EstadoTema = Tema['estado']
export type EstadoContenido = Contenido['estado']

export interface DatosTienda {
  nombre: string
  tipo: Tienda['tipo']
  envia_a_chile: boolean
  enlace_web?: string | null
  region?: string | null
}

export interface DatosGrupo {
  nombre: string
  region?: string | null
  plataforma: Grupo['plataforma']
  enlace?: string | null
}

/** Convierte un `datetime-local` del navegador a ISO 8601 con zona explícita. */
export function fechaLocalAISO(valor: string): string {
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return ''
  return fecha.toISOString()
}

/** `2026-11` a partir de la fecha actual, para precargar el formulario. */
export function mesActual(): string {
  return new Date().toISOString().slice(0, 7)
}

export const adminApi = {
  // --- Portada ---------------------------------------------------------
  resumen: () => peticionModulo<ResumenAdmin>(`${RAIZ}/resumen`),

  // --- Cuentas ---------------------------------------------------------
  usuarios: () =>
    peticionModulo<PaginaUsuariosAdmin>(`${RAIZ}/usuarios?limite=100`),

  cambiarEstadoUsuario: (id_usuario: string, activo: boolean) =>
    peticionModulo<Usuario>(`${RAIZ}/usuarios/${encodeURIComponent(id_usuario)}`, {
      method: 'PATCH',
      body: JSON.stringify({ activo }),
    }),

  // --- Bandeja editorial -----------------------------------------------
  contenido: () =>
    peticionModulo<PaginaContenido>(`${RAIZ}/contenido?limite=100`),

  publicarContenido: (id: string) =>
    peticionModulo<Contenido>(`${RAIZ}/contenido/${encodeURIComponent(id)}/publicar`, {
      method: 'POST',
    }),

  rechazarContenido: (id: string) =>
    peticionModulo<Contenido>(`${RAIZ}/contenido/${encodeURIComponent(id)}/rechazar`, {
      method: 'POST',
    }),

  volverABorrador: (id: string) =>
    peticionModulo<Contenido>(`${RAIZ}/contenido/${encodeURIComponent(id)}/borrador`, {
      method: 'POST',
    }),

  categorias: () => peticionModulo<Categoria[]>(`${RAIZ}/categorias`),

  crearCategoria: (nombre: string, descripcion?: string) =>
    peticionModulo<Categoria>(`${RAIZ}/categorias`, {
      method: 'POST',
      body: JSON.stringify({ nombre, descripcion: descripcion || null }),
    }),

  // --- Calendario ------------------------------------------------------
  eventos: () => peticionModulo<PaginaEventos>(`${RAIZ}/eventos?limite=100`),

  crearEvento: (datos: DatosEvento) =>
    peticionModulo<Evento>(`${RAIZ}/eventos`, {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  eliminarEvento: (id: string) =>
    peticionModulo<void>(`${RAIZ}/eventos/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),

  // --- Foro ------------------------------------------------------------
  temas: () => peticionModulo<PaginaTemas>(`${RAIZ}/foro/temas?limite=100`),

  cambiarEstadoTema: (id: string, estado: EstadoTema) =>
    peticionModulo<Tema>(`${RAIZ}/foro/temas/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ estado }),
    }),

  // --- Desafíos --------------------------------------------------------
  desafios: () => peticionModulo<PaginaDesafios>(`${RAIZ}/desafios`),

  crearDesafio: (datos: DatosDesafio) =>
    peticionModulo<Desafio>(`${RAIZ}/desafios`, {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  asignarGanador: (id: string, id_usuario: string) =>
    peticionModulo<Desafio>(`${RAIZ}/desafios/${encodeURIComponent(id)}/ganador`, {
      method: 'POST',
      body: JSON.stringify({ id_usuario }),
    }),

  // --- Comunidad -------------------------------------------------------
  crearTienda: (datos: DatosTienda) =>
    peticionModulo<Tienda>(`${RAIZ}/tiendas`, {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  crearGrupo: (datos: DatosGrupo) =>
    peticionModulo<Grupo>(`${RAIZ}/grupos`, {
      method: 'POST',
      body: JSON.stringify(datos),
    }),
}

/** Carga conjunta del panel. Se pide todo de una vez para una demo ágil. */
export interface DatosPanel {
  resumen: ResumenAdmin
  usuarios: PaginaUsuariosAdmin
  contenido: PaginaContenido
  eventos: PaginaEventos
  temas: PaginaTemas
  desafios: PaginaDesafios
  tiendas: PaginaTiendas
  grupos: PaginaGrupos
  categorias: Categoria[]
}

export async function cargarPanel(): Promise<DatosPanel> {
  const [
    resumen,
    usuarios,
    contenido,
    eventos,
    temas,
    desafios,
    tiendas,
    grupos,
    categorias,
  ] = await Promise.all([
    adminApi.resumen(),
    adminApi.usuarios(),
    adminApi.contenido(),
    adminApi.eventos(),
    adminApi.temas(),
    adminApi.desafios(),
    peticionModulo<PaginaTiendas>('/api/v1/tiendas'),
    peticionModulo<PaginaGrupos>('/api/v1/grupos'),
    adminApi.categorias(),
  ])
  return { resumen, usuarios, contenido, eventos, temas, desafios, tiendas, grupos, categorias }
}
