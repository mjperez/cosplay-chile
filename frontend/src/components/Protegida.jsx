import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexto/AuthContext'
import { Alerta, Cargando } from './ui'

export function RequiereSesion({ children }) {
  const { usuario, cargando } = useAuth()
  const location = useLocation()
  if (cargando) return <div className="contenedor"><Cargando /></div>
  if (!usuario) {
    return <Navigate to={`/ingresar?siguiente=${encodeURIComponent(location.pathname + location.search)}`} replace />
  }
  return children
}

export function RequiereAdmin({ children }) {
  const { usuario, cargando, esAdmin } = useAuth()
  const location = useLocation()
  if (cargando) return <div className="contenedor"><Cargando /></div>
  if (!usuario) return <Navigate to={`/ingresar?siguiente=${encodeURIComponent(location.pathname)}`} replace />
  if (!esAdmin) {
    return (
      <div className="contenedor py-16">
        <Alerta tipo="error">Esta sección es solo para el equipo de moderación.</Alerta>
      </div>
    )
  }
  return children
}
