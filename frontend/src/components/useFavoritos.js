import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../contexto/AuthContext'

const VACIO = { CONTENIDO: [], DIRECTORIO: [], EVENTO: [] }

// Ids de los favoritos de la sesión, para marcar los corazones de los listados.
// Devuelve una función esFavorito(tipo, id).
export default function useFavoritos() {
  const { usuario } = useAuth()
  const [ids, setIds] = useState(VACIO)
  useEffect(() => {
    if (!usuario) {
      setIds(VACIO)
      return
    }
    const control = new AbortController()
    api('/api/favoritos/ids', { signal: control.signal })
      .then((r) => setIds({ ...VACIO, ...r }))
      .catch(() => {})
    return () => control.abort()
  }, [usuario])
  return (tipo, id) => (ids[tipo] || []).includes(String(id))
}
