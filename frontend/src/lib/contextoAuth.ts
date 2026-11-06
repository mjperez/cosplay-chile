import { createContext, useContext } from 'react'

import type { DatosRegistro, Usuario } from './api'

export interface ContextoAuth {
  usuario: Usuario | null
  /** true mientras se valida el token guardado al cargar la página. */
  cargando: boolean
  iniciarSesion: (correo: string, password: string) => Promise<void>
  registrar: (datos: DatosRegistro) => Promise<void>
  cerrarSesion: () => void
}

/**
 * Contexto y hook viven separados del proveedor.
 *
 * Si el archivo exportara el componente y el hook a la vez, el recambio en
 * caliente de Vite (Fast Refresh) dejaría de funcionar: un módulo que mezcla
 * componentes y funciones no se puede reemplazar sin recargar la página.
 */
export const Contexto = createContext<ContextoAuth | null>(null)

export function useAuth(): ContextoAuth {
  const contexto = useContext(Contexto)
  if (!contexto) {
    throw new Error('useAuth debe usarse dentro de ProveedorAuth')
  }
  return contexto
}
