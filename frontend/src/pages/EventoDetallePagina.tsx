import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Campo } from '../components/ui/Campo'
import { Etiqueta } from '../components/ui/Etiqueta'
import { Tarjeta } from '../components/ui/Tarjeta'
import { ErrorApi } from '../lib/api'
import { useAuth } from '../lib/contextoAuth'
import {
  ETIQUETAS_TIPO_EVENTO,
  TONO_TIPO_EVENTO,
  enlaceExterno,
  formatearFecha,
  formatearFechaHora,
  mensajeDeFallo,
  modulosApi,
  type Evento,
  type PaginaParticipaciones,
} from '../lib/modulos'

/** Detalle de un evento, participantes e inscripción del usuario en sesión. */
export function EventoDetallePagina() {
  const { id = '' } = useParams()
  const { usuario, cargando: cargandoAuth } = useAuth()

  const [evento, setEvento] = useState<Evento | null>(null)
  const [participaciones, setParticipaciones] = useState<PaginaParticipaciones | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [reintento, setReintento] = useState(0)

  const [personaje, setPersonaje] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [errorAccion, setErrorAccion] = useState('')
  const [aviso, setAviso] = useState('')

  useEffect(() => {
    if (!id) return
    let vigente = true
    // El reinicio va en microtarea para no provocar un render en cascada
    // dentro del effect (regla de React Compiler).
    queueMicrotask(() => {
      if (!vigente) return
      setCargando(true)
      setError('')
      Promise.all([modulosApi.evento(id), modulosApi.participaciones(id)])
        .then(([datosEvento, datosParticipaciones]) => {
          if (!vigente) return
          setEvento(datosEvento)
          setParticipaciones(datosParticipaciones)
          setCargando(false)
        })
        .catch((fallo: unknown) => {
          if (!vigente) return
          if (fallo instanceof ErrorApi && fallo.estado === 404) {
            setError('No encontramos ese evento. Puede que lo hayan eliminado o que el enlace esté incompleto.')
          } else {
            setError(mensajeDeFallo(fallo, 'No pudimos cargar el evento. Revisa tu conexión.'))
          }
          setCargando(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [id, reintento])

  const inscrito = Boolean(
    usuario &&
      participaciones?.elementos.some((item) => item.id_usuario === usuario.id_usuario),
  )

  /** Mensajes claros para 401/409: son los dos fallos esperables de este flujo. */
  function explicarFalloAccion(fallo: unknown, accion: 'inscribir' | 'cancelar'): string {
    if (fallo instanceof ErrorApi) {
      if (fallo.estado === 401) {
        return 'Tu sesión venció. Vuelve a ingresar para continuar.'
      }
      if (fallo.estado === 403) {
        return 'Tu cuenta no tiene permiso para realizar esta acción.'
      }
      if (fallo.estado === 409) {
        return accion === 'inscribir'
          ? 'Ya estás inscrito/a en este evento. Recargamos la lista para que lo veas.'
          : 'No pudimos cancelar porque la inscripción cambió. Recargamos la información.'
      }
      if (fallo.estado === 404) {
        return accion === 'inscribir'
          ? 'Este evento ya no existe. Vuelve al calendario para elegir otro.'
          : 'Tu inscripción ya no figura en este evento.'
      }
      return fallo.message
    }
    return accion === 'inscribir'
      ? 'No pudimos completar la inscripción. Revisa tu conexión.'
      : 'No pudimos cancelar la inscripción. Revisa tu conexión.'
  }

  async function inscribirse(formulario: FormEvent) {
    formulario.preventDefault()
    if (!id) return
    setErrorAccion('')
    setAviso('')
    setEnviando(true)
    try {
      await modulosApi.participar(id, personaje.trim() || undefined)
      setPersonaje('')
      setAviso('¡Listo! Quedaste inscrito/a en el evento.')
      setReintento((valor) => valor + 1)
    } catch (fallo: unknown) {
      setErrorAccion(explicarFalloAccion(fallo, 'inscribir'))
      if (fallo instanceof ErrorApi && (fallo.estado === 409 || fallo.estado === 404)) {
        setReintento((valor) => valor + 1)
      }
    } finally {
      setEnviando(false)
    }
  }

  async function cancelarInscripcion() {
    if (!id) return
    setErrorAccion('')
    setAviso('')
    setEnviando(true)
    try {
      await modulosApi.cancelarParticipacion(id)
      setAviso('Cancelamos tu inscripción. Ya no apareces en la lista.')
      setReintento((valor) => valor + 1)
    } catch (fallo: unknown) {
      setErrorAccion(explicarFalloAccion(fallo, 'cancelar'))
      if (fallo instanceof ErrorApi && (fallo.estado === 409 || fallo.estado === 404)) {
        setReintento((valor) => valor + 1)
      }
    } finally {
      setEnviando(false)
    }
  }

  const enlaceOficial = evento ? enlaceExterno(evento.enlace_oficial) : null

  return (
    <Disposicion>
      <div className="mx-auto max-w-4xl px-4 py-12">
        <Link to="/eventos" className="text-sm font-semibold text-marca-700 hover:underline">
          <span aria-hidden="true">← </span>Volver al calendario
        </Link>

        {!id && (
          <div role="alert" className="mt-8 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-12 text-center">
            <p className="text-base font-semibold text-tinta-900">Falta el identificador del evento</p>
            <p className="mt-2 text-sm text-tinta-600">
              El enlace no indica qué evento quieres ver. Prueba desde el calendario.
            </p>
          </div>
        )}

        {id && cargando && (
          <p aria-live="polite" className="mt-8 text-sm text-tinta-600">
            {evento ? 'Actualizando el evento…' : 'Cargando el evento…'}
          </p>
        )}

        {id && error && (
          <div role="alert" className="mt-8 rounded-control bg-error-50 px-4 py-4 text-sm text-error-600">
            <p className="font-medium">{error}</p>
            <div className="mt-4">
              <Boton variante="secundario" tamano="sm" onClick={() => setReintento((valor) => valor + 1)}>
                Reintentar
              </Boton>
            </div>
          </div>
        )}

        {/* Si falla una recarga posterior se conserva lo ya mostrado: el error
            queda arriba con su botón de reintento, la página no queda vacía. */}
        {id && evento && participaciones && (
          <>
            <Tarjeta como="article" className="mt-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <Etiqueta tono={TONO_TIPO_EVENTO[evento.tipo] ?? 'neutro'}>
                  {ETIQUETAS_TIPO_EVENTO[evento.tipo] ?? evento.tipo}
                </Etiqueta>
                <span className="text-sm font-medium text-tinta-500">
                  Publicado el {formatearFecha(evento.creado_en)}
                </span>
              </div>

              <h1 className="mt-4 text-3xl font-black tracking-tight text-tinta-900">
                {evento.nombre}
              </h1>

              <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2">
                <div>
                  <dt className="font-semibold text-tinta-800">Inicio</dt>
                  <dd className="mt-1 text-tinta-600">{formatearFechaHora(evento.fecha_inicio)}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-tinta-800">Término</dt>
                  <dd className="mt-1 text-tinta-600">
                    {evento.fecha_fin ? formatearFechaHora(evento.fecha_fin) : 'No informado'}
                  </dd>
                </div>
                <div>
                  <dt className="font-semibold text-tinta-800">Lugar</dt>
                  <dd className="mt-1 text-tinta-600">{evento.lugar}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-tinta-800">Región</dt>
                  <dd className="mt-1 text-tinta-600">{evento.region || 'No informada'}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-tinta-800">Inscritos</dt>
                  <dd className="mt-1 text-tinta-600">
                    {evento.total_participantes === 1
                      ? '1 persona'
                      : `${evento.total_participantes} personas`}
                  </dd>
                </div>
                {enlaceOficial && (
                  <div>
                    <dt className="font-semibold text-tinta-800">Sitio oficial</dt>
                    <dd className="mt-1">
                      <a
                        href={enlaceOficial}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-semibold text-marca-700 hover:underline"
                      >
                        Visitar enlace oficial <span aria-hidden="true">↗</span>
                      </a>
                    </dd>
                  </div>
                )}
              </dl>
            </Tarjeta>

            {/* --- Inscripción ------------------------------------------ */}
            <section aria-labelledby="titulo-inscripcion" className="mt-8">
              <Tarjeta>
                <h2 id="titulo-inscripcion" className="text-lg font-bold text-tinta-900">
                  Participar
                </h2>

                {aviso && (
                  <p
                    role="status"
                    className="mt-4 rounded-control border border-tinta-200 bg-white px-3 py-2 text-sm font-medium text-exito-600"
                  >
                    {aviso}
                  </p>
                )}

                {errorAccion && (
                  <p role="alert" className="mt-4 rounded-control bg-error-50 px-3 py-2 text-sm font-medium text-error-600">
                    {errorAccion}
                  </p>
                )}

                {cargandoAuth ? (
                  <p aria-live="polite" className="mt-4 text-sm text-tinta-600">
                    Revisando tu sesión…
                  </p>
                ) : !usuario ? (
                  <p className="mt-3 text-sm leading-relaxed text-tinta-600">
                    Tienes que{' '}
                    <Link
                      to="/ingresar"
                      state={{ desde: `/eventos/${id}` }}
                      className="font-semibold text-marca-700 hover:underline"
                    >
                      ingresar
                    </Link>{' '}
                    para inscribirte y aparecer en la lista de participantes.
                  </p>
                ) : inscrito ? (
                  <div className="mt-4 flex flex-wrap items-center gap-4">
                    <p className="text-sm text-tinta-700">
                      Ya estás inscrito/a. ¡Nos vemos en el evento!
                    </p>
                    <Boton
                      variante="secundario"
                      onClick={cancelarInscripcion}
                      cargando={enviando}
                      disabled={cargando}
                    >
                      Cancelar inscripción
                    </Boton>
                  </div>
                ) : (
                  <form onSubmit={inscribirse} className="mt-4 flex flex-col gap-4" noValidate>
                    <Campo
                      etiqueta="Personaje (opcional)"
                      id="personaje-inscripcion"
                      ayuda="Cuéntanos de quién vas disfrazado/a. Puedes dejarlo en blanco."
                      maxLength={120}
                      value={personaje}
                      onChange={(eventoCampo) => setPersonaje(eventoCampo.target.value)}
                    />
                    <div>
                      <Boton type="submit" cargando={enviando} disabled={cargando}>
                        Inscribirme
                      </Boton>
                    </div>
                  </form>
                )}
              </Tarjeta>
            </section>

            {/* --- Participantes ---------------------------------------- */}
            <section aria-labelledby="titulo-participantes" className="mt-10">
              <h2 id="titulo-participantes" className="text-xl font-bold text-tinta-900">
                Quiénes van ({participaciones.total})
              </h2>

              {participaciones.total === 0 ? (
                <div className="mt-4 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-10 text-center">
                  <p className="text-sm font-semibold text-tinta-900">
                    Todavía nadie se ha inscrito
                  </p>
                  <p className="mt-2 text-sm text-tinta-600">
                    Puedes ser la primera persona en sumarte a este evento.
                  </p>
                </div>
              ) : (
                <ul className="mt-4 grid gap-3 sm:grid-cols-2">
                  {participaciones.elementos.map((participacion) => (
                    <Tarjeta como="li" key={participacion.id_participacion} className="p-4">
                      <p className="text-sm font-semibold text-tinta-900">
                        {participacion.nombre_usuario}
                      </p>
                      <p className="mt-1 text-sm text-tinta-600">
                        {participacion.personaje
                          ? `Como ${participacion.personaje}`
                          : 'Sin personaje declarado'}
                      </p>
                    </Tarjeta>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </Disposicion>
  )
}
