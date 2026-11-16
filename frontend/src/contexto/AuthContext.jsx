import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, guardarToken, obtenerToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(Boolean(obtenerToken()))
  const [sesionExpirada, setSesionExpirada] = useState(false)

  const cerrarSesion = useCallback(() => {
    guardarToken(null)
    setUsuario(null)
  }, [])

  const refrescar = useCallback(async () => {
    if (!obtenerToken()) {
      setCargando(false)
      return null
    }
    try {
      const u = await api('/api/auth/me')
      setUsuario(u)
      return u
    } catch {
      guardarToken(null)
      setUsuario(null)
      return null
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    refrescar()
  }, [refrescar])

  useEffect(() => {
    const alExpirar = () => {
      guardarToken(null)
      setUsuario(null)
      setSesionExpirada(true)
    }
    window.addEventListener('sesion-expirada', alExpirar)
    return () => window.removeEventListener('sesion-expirada', alExpirar)
  }, [])

  const iniciarSesion = useCallback(async (email, password) => {
    const r = await api('/api/auth/login', { method: 'POST', body: { email, password } })
    guardarToken(r.access_token)
    setUsuario(r.usuario)
    setSesionExpirada(false)
    return r.usuario
  }, [])

  const registrarse = useCallback(async (datos) => {
    const r = await api('/api/auth/registro', { method: 'POST', body: datos })
    guardarToken(r.access_token)
    setUsuario(r.usuario)
    return r.usuario
  }, [])

  const valor = useMemo(
    () => ({
      usuario,
      cargando,
      esAdmin: usuario?.rol === 'ADMIN',
      sesionExpirada,
      limpiarAvisoSesion: () => setSesionExpirada(false),
      iniciarSesion,
      registrarse,
      cerrarSesion,
      refrescar,
      setUsuario,
    }),
    [usuario, cargando, sesionExpirada, iniciarSesion, registrarse, cerrarSesion, refrescar],
  )
  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
