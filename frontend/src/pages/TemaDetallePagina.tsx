import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Etiqueta } from '../components/ui/Etiqueta'
import { Tarjeta } from '../components/ui/Tarjeta'
import { ErrorApi } from '../lib/api'
import { useAuth } from '../lib/contextoAuth'
import {
  formatearFechaHora,
  mensajeDeFallo,
  modulosApi,
  type TemaDetalle,
} from '../lib/modulos'

/** Tema completo, sus respuestas y el formulario para responder. */
export function TemaDetallePagina() {
  const { id = '' } = useParams()
  const { usuario, cargando: cargandoAuth } = useAuth()

  const [tema, setTema] = useState<TemaDetalle | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [reintento, setReintento] = useState(0)

  const [contenido, setContenido] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [errorAccion, setErrorAccion] = useState('')
  const [aviso, setAviso] = useState('')
  const [cerrando, setCerrando] = useState(false)
  const [avisoCierre, setAvisoCierre] = useState('')
  const [errorCierre, setErrorCierre] = useState('')

  useEffect(() => {
    if (!id) return
    let vigente = true
    // El reinicio va en microtarea para no provocar un render en cascada
    // dentro del effect (regla de React Compiler).
    queueMicrotask(() => {
      if (!vigente) return
      setCargando(true)
      setError('')
      modulosApi
        .tema(id)
        .then((datosTema) => {
          if (!vigente) return
          setTema(datosTema)
          setCargando(false)
        })
        .catch((fallo: unknown) => {
          if (!vigente) return
          if (fallo instanceof ErrorApi && fallo.estado === 404) {
            setError('No encontramos ese tema. Puede que lo hayan eliminado o que no esté disponible.')
          } else {
            setError(mensajeDeFallo(fallo, 'No pudimos cargar la conversación. Revisa tu conexión.'))
          }
          setCargando(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [id, reintento])

  async function responder(formulario: FormEvent) {
    formulario.preventDefault()
    if (!id) return
    setErrorAccion('')
    setAviso('')

    const contenidoLimpio = contenido.trim()
    if (!contenidoLimpio) {
      setErrorAccion('Escribe tu respuesta antes de enviarla.')
      return
    }

    setEnviando(true)
    try {
      await modulosApi.responderTema(id, contenidoLimpio)
      setContenido('')
      setAviso('Tu respuesta ya está publicada.')
      setReintento((valor) => valor + 1)
    } catch (fallo: unknown) {
      if (fallo instanceof ErrorApi && fallo.estado === 401) {
        setErrorAccion('Tu sesión venció. Vuelve a ingresar para responder.')
      } else if (fallo instanceof ErrorApi && fallo.estado === 409) {
        setErrorAccion('Este tema se cerró mientras escribías. Actualizamos la conversación.')
        setReintento((valor) => valor + 1)
      } else if (fallo instanceof ErrorApi && fallo.estado === 403) {
        setErrorAccion('Tu cuenta no puede responder en este tema.')
      } else {
        setErrorAccion(mensajeDeFallo(fallo, 'No pudimos publicar tu respuesta. Revisa tu conexión.'))
      }
    } finally {
      setEnviando(false)
    }
  }

  async function cerrar() {
    if (!id) return
    setErrorCierre('')
    setAvisoCierre('')
    setCerrando(true)
    try {
      await modulosApi.cerrarTema(id)
      setAvisoCierre('El tema quedó cerrado. Ya no acepta respuestas nuevas.')
      setReintento((valor) => valor + 1)
    } catch (fallo: unknown) {
      if (fallo instanceof ErrorApi && fallo.estado === 403) {
        setErrorCierre('Solo el autor del tema o un administrador pueden cerrarlo.')
      } else if (fallo instanceof ErrorApi && fallo.estado === 401) {
        setErrorCierre('Tu sesión venció. Vuelve a ingresar para cerrar el tema.')
      } else {
        setErrorCierre(mensajeDeFallo(fallo, 'No pudimos cerrar el tema. Revisa tu conexión.'))
      }
    } finally {
      setCerrando(false)
    }
  }

  const puedeCerrar =
    !!usuario &&
    tema?.estado === 'abierto' &&
    (usuario.id_usuario === tema.id_creador || usuario.rol === 'administrador')

  return (
    <Disposicion>
      <div className="mx-auto max-w-3xl px-4 py-12">
        <Link to="/foro" className="text-sm font-semibold text-marca-700 hover:underline">
          <span aria-hidden="true">← </span>Volver al foro
        </Link>

        {!id && (
          <div role="alert" className="mt-8 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-12 text-center">
            <p className="text-base font-semibold text-tinta-900">Falta el identificador del tema</p>
            <p className="mt-2 text-sm text-tinta-600">
              El enlace no indica qué conversación quieres leer.
            </p>
          </div>
        )}

        {id && cargando && (
          <p aria-live="polite" className="mt-8 text-sm text-tinta-600">
            {tema ? 'Actualizando la conversación…' : 'Cargando la conversación…'}
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

        {/* Ante una recarga fallida se mantiene la conversación en pantalla. */}
        {id && tema && (
          <>
            <Tarjeta como="article" className="mt-6">
              <div className="flex flex-wrap items-center gap-2">
                <Etiqueta tono="marca">{tema.categoria}</Etiqueta>
                {tema.estado === 'cerrado' && <Etiqueta tono="neutro">Cerrado</Etiqueta>}
                {tema.estado === 'oculto' && <Etiqueta tono="neutro">No disponible</Etiqueta>}
                <span className="text-xs text-tinta-500">
                  {tema.total_respuestas === 1
                    ? '1 respuesta'
                    : `${tema.total_respuestas} respuestas`}
                </span>
              </div>

              <h1 className="mt-4 text-3xl font-black tracking-tight text-tinta-900">
                {tema.titulo}
              </h1>
              <p className="mt-2 text-sm text-tinta-500">
                Por {tema.nombre_autor} · {formatearFechaHora(tema.creado_en)}
              </p>

              {puedeCerrar && (
                <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-tinta-100 pt-4">
                  <Boton
                    variante="secundario"
                    tamano="sm"
                    cargando={cerrando}
                    onClick={cerrar}
                  >
                    Cerrar tema
                  </Boton>
                  <span className="text-xs text-tinta-500">
                    Al cerrarlo se conservan las respuestas, pero no se aceptan nuevas.
                  </span>
                </div>
              )}
              {avisoCierre && (
                <p role="status" className="mt-3 text-sm font-medium text-exito-600">
                  {avisoCierre}
                </p>
              )}
              {errorCierre && (
                <p role="alert" className="mt-3 rounded-control bg-error-50 px-3 py-2 text-sm font-medium text-error-600">
                  {errorCierre}
                </p>
              )}

              {tema.contenido ? (
                <p className="mt-6 whitespace-pre-wrap text-base leading-relaxed text-tinta-700">
                  {tema.contenido}
                </p>
              ) : (
                <p className="mt-6 text-sm italic text-tinta-500">
                  Este tema no tiene texto de apertura.
                </p>
              )}
            </Tarjeta>

            <section aria-labelledby="titulo-respuestas" className="mt-10">
              <h2 id="titulo-respuestas" className="text-xl font-bold text-tinta-900">
                Respuestas ({tema.respuestas.length})
              </h2>

              {tema.respuestas.length === 0 ? (
                <div className="mt-4 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-10 text-center">
                  <p className="text-sm font-semibold text-tinta-900">
                    Todavía no hay respuestas
                  </p>
                  <p className="mt-2 text-sm text-tinta-600">
                    Si sabes algo que pueda ayudar, deja la primera respuesta.
                  </p>
                </div>
              ) : (
                <ul className="mt-4 flex flex-col gap-3">
                  {tema.respuestas.map((respuesta) => (
                    <Tarjeta como="li" key={respuesta.id_respuesta}>
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <p className="text-sm font-semibold text-tinta-900">
                          {respuesta.nombre_autor}
                        </p>
                        <p className="text-xs text-tinta-500">
                          {formatearFechaHora(respuesta.creado_en)}
                        </p>
                      </div>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-tinta-700">
                        {respuesta.contenido}
                      </p>
                    </Tarjeta>
                  ))}
                </ul>
              )}
            </section>

            <section aria-labelledby="titulo-responder" className="mt-10">
              <Tarjeta>
                <h2 id="titulo-responder" className="text-lg font-bold text-tinta-900">
                  Responder
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
                    Para responder tienes que{' '}
                    <Link
                      to="/ingresar"
                      state={{ desde: `/foro/${id}` }}
                      className="font-semibold text-marca-700 hover:underline"
                    >
                      ingresar
                    </Link>
                    . La lectura es abierta para todos.
                  </p>
                ) : tema.estado !== 'abierto' ? (
                  <p className="mt-3 text-sm leading-relaxed text-tinta-600">
                    Este tema está cerrado, así que ya no se aceptan respuestas.
                    Puedes abrir uno nuevo desde el foro si quieres seguir la conversación.
                  </p>
                ) : (
                  <form onSubmit={responder} className="mt-4 flex flex-col gap-4" noValidate>
                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="contenido-respuesta" className="text-sm font-medium text-tinta-800">
                        Tu respuesta
                      </label>
                      <textarea
                        id="contenido-respuesta"
                        rows={5}
                        required
                        maxLength={5000}
                        value={contenido}
                        onChange={(evento) => setContenido(evento.target.value)}
                        placeholder="Aporta con tu experiencia, una duda o un dato que falte."
                        className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 placeholder:text-tinta-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                      />
                    </div>
                    <div>
                      <Boton type="submit" cargando={enviando} disabled={cargando}>
                        Publicar respuesta
                      </Boton>
                    </div>
                  </form>
                )}
              </Tarjeta>
            </section>
          </>
        )}
      </div>
    </Disposicion>
  )
}
