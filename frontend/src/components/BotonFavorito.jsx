import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../contexto/AuthContext'
import Icono from './diseno/Icono'

// RF-25: guardar guías, proveedores o eventos (requiere sesión).
// variante «icono»: botón redondo con corazón (tarjetas) · «boton»: botón con texto (fichas de detalle)
export default function BotonFavorito({ tipo, objetoId, inicial = false, nombre = '', variante = 'boton' }) {
  const { usuario } = useAuth()
  const location = useLocation()
  const [activo, setActivo] = useState(inicial)
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')

  // El estado inicial puede llegar después (p. ej. cuando se cargan los ids de favoritos)
  useEffect(() => setActivo(inicial), [inicial])

  const aIngresar = `/ingresar?siguiente=${encodeURIComponent(location.pathname + location.search)}`
  if (!usuario) {
    if (variante === 'icono') {
      return (
        <Link to={aIngresar} className="boton-icono" aria-label={`Inicia sesión para guardar en favoritos${nombre ? `: ${nombre}` : ''}`}>
          <Icono nombre="corazon" tamano={18} />
        </Link>
      )
    }
    return (
      <Link to={aIngresar} className="boton-contorno">
        <Icono nombre="corazon" tamano={16} /> Inicia sesión para guardar
      </Link>
    )
  }

  const alternar = async () => {
    setOcupado(true)
    setError('')
    try {
      if (activo) await api(`/api/favoritos/${tipo}/${objetoId}`, { method: 'DELETE' })
      else await api('/api/favoritos', { method: 'POST', body: { tipo, objeto_id: objetoId } })
      setActivo(!activo)
    } catch (e) {
      setError(e.message)
    } finally {
      setOcupado(false)
    }
  }

  if (variante === 'icono') {
    return (
      <span className="relative inline-flex">
        <button
          type="button"
          className="boton-icono"
          aria-pressed={activo}
          aria-label={`Guardar en favoritos${nombre ? `: ${nombre}` : ''}`}
          onClick={alternar}
          disabled={ocupado}
        >
          <Icono nombre="corazon" tamano={18} relleno={activo ? 'currentColor' : 'none'} />
        </button>
        {error && <span role="alert" className="absolute right-0 top-12 z-10 w-48 rounded-lg bg-panel p-2 text-xs text-peligro">{error}</span>}
      </span>
    )
  }

  return (
    <span className="inline-flex flex-col">
      <button type="button" className={activo ? 'boton-marca' : 'boton-contorno'} aria-pressed={activo} onClick={alternar} disabled={ocupado}>
        <Icono nombre="corazon" tamano={16} relleno={activo ? 'currentColor' : 'none'} />
        {activo ? 'Guardado en favoritos' : 'Guardar en favoritos'}
        {nombre && <span className="sr-only">: {nombre}</span>}
      </button>
      {error && <span role="alert" className="mensaje-error">{error}</span>}
    </span>
  )
}
