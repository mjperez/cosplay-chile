/**
 * Cliente HTTP del backend.
 *
 * El token se guarda en localStorage para que la sesión sobreviva a una
 * recarga. Al arrancar, `ProveedorAuth` lo valida contra `/auth/me`: si el
 * token venció, se descarta y el usuario vuelve a entrar.
 */

export const CLAVE_TOKEN = 'cosplay.token'

export type Rol =
  | 'visitante'
  | 'cosplayer'
  | 'cosmaker'
  | 'sastre'
  | 'tienda'
  | 'fotografo'
  | 'organizador'
  | 'administrador'

export interface Usuario {
  id_usuario: string
  nombre: string
  correo: string
  rol: Rol
  region: string
  activo: boolean
  creado_en: string
}

export interface RespuestaToken {
  access_token: string
  token_type: string
  expires_in: number
  usuario: Usuario
}

export interface PoliticaPrivacidad {
  version: string
  fecha: string
  titulo: string
  texto: string
}

export interface DatosRegistro {
  nombre: string
  correo: string
  password: string
  rol: Exclude<Rol, 'administrador'>
  region: string
  acepta_privacidad: boolean
  consentimiento_version: string
}

export class ErrorApi extends Error {
  readonly estado: number

  constructor(estado: number, mensaje: string) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
  }
}

const BASE = import.meta.env.VITE_API_URL ?? ''

export function leerToken(): string | null {
  return localStorage.getItem(CLAVE_TOKEN)
}

export function guardarToken(token: string): void {
  localStorage.setItem(CLAVE_TOKEN, token)
}

export function borrarToken(): void {
  localStorage.removeItem(CLAVE_TOKEN)
}

/** FastAPI devuelve `detail` como texto en los 4xx propios y como lista en los 422. */
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

async function peticion<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const cabeceras = new Headers(opciones.headers)
  if (opciones.body && !cabeceras.has('Content-Type')) {
    cabeceras.set('Content-Type', 'application/json')
  }
  const token = leerToken()
  if (token) cabeceras.set('Authorization', `Bearer ${token}`)

  const respuesta = await fetch(`${BASE}${ruta}`, { ...opciones, headers: cabeceras })
  const texto = await respuesta.text()
  const cuerpo: unknown = texto ? JSON.parse(texto) : null

  if (!respuesta.ok) {
    throw new ErrorApi(respuesta.status, mensajeDeError(cuerpo, respuesta.status))
  }
  return cuerpo as T
}

export const api = {
  salud: () => peticion<{ status: string; database: { ok: boolean } }>('/health'),

  politica: () => peticion<PoliticaPrivacidad>('/api/v1/privacidad'),

  registro: (datos: DatosRegistro) =>
    peticion<Usuario>('/api/v1/auth/registro', {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  login: (correo: string, password: string) =>
    peticion<RespuestaToken>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ correo, password }),
    }),

  yo: () => peticion<Usuario>('/api/v1/auth/me'),
}
