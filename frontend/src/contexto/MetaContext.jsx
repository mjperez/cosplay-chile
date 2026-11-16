import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const MetaContext = createContext({ meta: null, etiqueta: (_g, v) => v, opciones: () => [] })

export function MetaProvider({ children }) {
  const [meta, setMeta] = useState(null)
  useEffect(() => {
    api('/api/meta').then(setMeta).catch(() => setMeta(null))
  }, [])
  const etiqueta = (grupo, valor) => meta?.[grupo]?.[valor] ?? valor ?? ''
  const opciones = (grupo) => Object.entries(meta?.[grupo] || {}).map(([valor, texto]) => ({ valor, texto }))
  return <MetaContext.Provider value={{ meta, etiqueta, opciones }}>{children}</MetaContext.Provider>
}

export function useMeta() {
  return useContext(MetaContext)
}
