import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

// Carga una ruta GET y expone {datos, error, cargando, recargar}. ruta = null no carga nada.
export default function useApi(ruta) {
  const [estado, setEstado] = useState({ datos: null, error: null, cargando: Boolean(ruta) })
  const [version, setVersion] = useState(0)

  useEffect(() => {
    if (!ruta) {
      setEstado({ datos: null, error: null, cargando: false })
      return
    }
    const control = new AbortController()
    setEstado((e) => ({ ...e, cargando: true, error: null }))
    api(ruta, { signal: control.signal })
      .then((datos) => setEstado({ datos, error: null, cargando: false }))
      .catch((error) => {
        if (error.name !== 'AbortError') setEstado({ datos: null, error, cargando: false })
      })
    return () => control.abort()
  }, [ruta, version])

  const recargar = useCallback(() => setVersion((v) => v + 1), [])
  return { ...estado, recargar }
}
