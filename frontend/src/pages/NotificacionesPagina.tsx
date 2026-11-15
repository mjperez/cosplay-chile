import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Tarjeta } from '../components/ui/Tarjeta'
import { useAuth } from '../lib/contextoAuth'
import { formatearFechaHora, mensajeDeFallo } from '../lib/modulos'
import { notificacionesApi, type Notificacion } from '../lib/notificaciones'

/** Bandeja de avisos internos que produce el patrón Observer (RF-37). */
export function NotificacionesPagina() {
  const { usuario, cargando: validandoSesion } = useAuth()
  const [avisos, setAvisos] = useState<Notificacion[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [marcando, setMarcando] = useState<string | null>(null)
  const [recarga, setRecarga] = useState(0)

  useEffect(() => {
    if (!usuario) return
    let vigente = true
    queueMicrotask(() => {
      if (!vigente) return
      setCargando(true)
      notificacionesApi
        .listar()
        .then((pagina) => {
          if (vigente) setAvisos(pagina.elementos)
        })
        .catch((fallo: unknown) => {
          if (vigente) setError(mensajeDeFallo(fallo, 'No pudimos cargar tus avisos.'))
        })
        .finally(() => {
          if (vigente) setCargando(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [usuario, recarga])

  if (validandoSesion) {
    return (
      <Disposicion>
        <p className="mx-auto max-w-3xl px-4 py-16 text-center text-tinta-600">
          Verificando sesión…
        </p>
      </Disposicion>
    )
  }
  if (!usuario) {
    return <Navigate to="/ingresar" replace state={{ desde: '/notificaciones' }} />
  }

  async function marcarLeida(id: string) {
    setMarcando(id)
    setError('')
    setAviso('')
    try {
      await notificacionesApi.marcarLeida(id)
      setAviso('Aviso marcado como leído.')
      setRecarga((valor) => valor + 1)
    } catch (fallo) {
      setError(mensajeDeFallo(fallo, 'No pudimos marcar el aviso como leído.'))
    } finally {
      setMarcando(null)
    }
  }

  const pendientes = avisos.filter((item) => !item.leida).length

  return (
    <Disposicion>
      <div className="mx-auto max-w-3xl px-4 py-10">
        <header>
          <p className="text-xs font-semibold uppercase tracking-wide text-marca-700">
            Mi cuenta
          </p>
          <h1 className="mt-1 text-3xl font-black tracking-tight text-tinta-900">
            Notificaciones
          </h1>
          <p className="mt-2 text-sm text-tinta-600">
            {pendientes > 0
              ? `Tienes ${pendientes} aviso${pendientes === 1 ? '' : 's'} sin leer.`
              : 'Estás al día: no tienes avisos pendientes.'}
          </p>
        </header>

        {aviso && (
          <p role="status" className="mt-6 rounded-control bg-marca-50 px-4 py-3 text-sm text-marca-800">
            {aviso}
          </p>
        )}
        {error && (
          <p role="alert" className="mt-6 rounded-control bg-error-50 px-4 py-3 text-sm text-error-600">
            {error}
          </p>
        )}

        {cargando ? (
          <p className="mt-8 text-sm text-tinta-600">Cargando avisos…</p>
        ) : avisos.length === 0 ? (
          <Tarjeta>
            <p className="text-sm text-tinta-600">
              Todavía no hay novedades. Cuando se publique una guía, un evento o
              un desafío, el aviso aparecerá aquí.
            </p>
          </Tarjeta>
        ) : (
          <ul className="mt-8 flex flex-col gap-3">
            {avisos.map((item) => (
              <li key={item.id_notificacion}>
                <Tarjeta>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-base font-bold text-tinta-900">
                          {item.titulo}
                        </h2>
                        {!item.leida && (
                          <span className="rounded-full bg-marca-100 px-2 py-0.5 text-xs font-semibold text-marca-800">
                            Nuevo
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-tinta-700">{item.mensaje}</p>
                      <p className="mt-2 text-xs text-tinta-500">
                        {formatearFechaHora(item.creado_en)}
                      </p>
                    </div>
                    {!item.leida && (
                      <Boton
                        variante="secundario"
                        tamano="sm"
                        cargando={marcando === item.id_notificacion}
                        onClick={() => {
                          void marcarLeida(item.id_notificacion)
                        }}
                      >
                        Marcar leída
                      </Boton>
                    )}
                  </div>
                </Tarjeta>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Disposicion>
  )
}
