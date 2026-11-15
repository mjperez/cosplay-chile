/** Avisos internos generados por el patrón Observer (RF-37). */

import { peticionModulo } from './modulos'

export interface Notificacion {
  id_notificacion: string
  tipo: string
  titulo: string
  mensaje: string
  id_recurso: string | null
  leida: boolean
  creado_en: string
}

export interface PaginaNotificaciones {
  total: number
  sin_leer: number
  limite: number
  desplazamiento: number
  elementos: Notificacion[]
}

export const notificacionesApi = {
  listar: () =>
    peticionModulo<PaginaNotificaciones>('/api/v1/notificaciones?limite=100'),

  sinLeer: () =>
    peticionModulo<{ sin_leer: number }>('/api/v1/notificaciones/sin-leer'),

  marcarLeida: (id: string) =>
    peticionModulo<Notificacion>(
      `/api/v1/notificaciones/${encodeURIComponent(id)}/leer`,
      { method: 'PATCH' },
    ),
}
