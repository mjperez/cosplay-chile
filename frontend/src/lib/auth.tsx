import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import {
  api,
  borrarToken,
  guardarToken,
  leerToken,
  type DatosRegistro,
  type Usuario,
} from './api'
import { Contexto } from './contextoAuth'

export function ProveedorAuth({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  // El estado inicial se deriva en el arranque: si no hay token guardado no
  // hay nada que validar, así que no se necesita un efecto que lo apague.
  const [cargando, setCargando] = useState(() => leerToken() !== null)

  // Con token guardado se comprueba contra el backend. Un token vencido
  // devuelve 401 y se descarta: la interfaz vuelve a estado invitado en lugar
  // de quedar en una sesión fantasma que falla en cada petición.
  useEffect(() => {
    if (!leerToken()) return

    let vigente = true
    api
      .yo()
      .then((datos) => {
        if (vigente) setUsuario(datos)
      })
      .catch(() => {
        borrarToken()
        if (vigente) setUsuario(null)
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
    }
  }, [])

  const iniciarSesion = useCallback(async (correo: string, password: string) => {
    const respuesta = await api.login(correo, password)
    guardarToken(respuesta.access_token)
    setUsuario(respuesta.usuario)
  }, [])

  const registrar = useCallback(async (datos: DatosRegistro) => {
    await api.registro(datos)
    const respuesta = await api.login(datos.correo, datos.password)
    guardarToken(respuesta.access_token)
    setUsuario(respuesta.usuario)
  }, [])

  const cerrarSesion = useCallback(() => {
    borrarToken()
    setUsuario(null)
  }, [])

  const valor = useMemo(
    () => ({ usuario, cargando, iniciarSesion, registrar, cerrarSesion }),
    [usuario, cargando, iniciarSesion, registrar, cerrarSesion],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}
