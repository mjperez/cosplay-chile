import DOMPurify from 'dompurify'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Etiqueta } from '../components/ui/Etiqueta'
import { api, type Contenido } from '../lib/api'
import { ETIQUETAS_CONTENIDO, ETIQUETAS_NIVEL, TONO_CONTENIDO } from '../lib/contenido'

/**
 * Bloque con título, usado para las secciones propias de cada tipo.
 */
function Seccion({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-tinta-500">{titulo}</h2>
      <div className="mt-3">{children}</div>
    </section>
  )
}

function Lista({ elementos }: { elementos: string[] | null }) {
  if (!elementos || elementos.length === 0) return null
  return (
    <ul className="space-y-2">
      {elementos.map((elemento, indice) => (
        <li key={indice} className="flex gap-2 text-sm leading-relaxed text-tinta-700">
          <span aria-hidden="true" className="mt-1 size-1.5 shrink-0 rounded-full bg-marca-400" />
          {elemento}
        </li>
      ))}
    </ul>
  )
}

export function ContenidoDetallePagina() {
  const { id } = useParams<{ id: string }>()
  const [contenido, setContenido] = useState<Contenido | null>(null)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    if (!id) return
    let vigente = true
    api
      .contenidoPorId(id)
      .then((datos) => {
        if (vigente) setContenido(datos)
      })
      .catch(() => {
        if (vigente) setError('Este contenido no existe o todavía no está publicado.')
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })
    return () => {
      vigente = false
    }
  }, [id])

  // El cuerpo se guarda como HTML. Se sanea antes de inyectarlo: el contenido
  // lo escribe un usuario y no se puede confiar en él. Sanear en el cliente no
  // reemplaza sanear en el servidor, pero evita el vector más obvio.
  const cuerpoSaneado = useMemo(
    () => (contenido?.cuerpo ? DOMPurify.sanitize(contenido.cuerpo) : ''),
    [contenido],
  )

  if (cargando) {
    return (
      <Disposicion>
        <p className="mx-auto max-w-2xl px-4 py-16 text-sm text-tinta-500">Cargando…</p>
      </Disposicion>
    )
  }

  if (error || !contenido) {
    return (
      <Disposicion>
        <div className="mx-auto max-w-2xl px-4 py-20 text-center">
          <h1 className="text-2xl font-bold text-tinta-900">No encontramos este contenido</h1>
          <p className="mt-3 text-sm text-tinta-600">{error}</p>
          <Link
            to="/contenido"
            className="mt-8 inline-block rounded-control bg-marca-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-marca-800"
          >
            Volver a contenidos
          </Link>
        </div>
      </Disposicion>
    )
  }

  return (
    <Disposicion>
      <article className="mx-auto max-w-2xl px-4 py-12">
        <div className="flex flex-wrap items-center gap-3">
          <Etiqueta tono={TONO_CONTENIDO[contenido.tipo] ?? 'neutro'}>
            {ETIQUETAS_CONTENIDO[contenido.tipo] ?? contenido.tipo}
          </Etiqueta>
          <span className="text-xs font-medium text-tinta-500">
            Nivel {ETIQUETAS_NIVEL[contenido.nivel] ?? contenido.nivel}
          </span>
        </div>

        <h1 className="mt-4 text-3xl font-black leading-tight tracking-tight text-tinta-900">
          {contenido.titulo}
        </h1>

        {contenido.resumen && (
          <p className="mt-4 text-lg leading-relaxed text-tinta-600">{contenido.resumen}</p>
        )}

        {cuerpoSaneado && (
          <div
            className="mt-8 space-y-4 text-base leading-relaxed text-tinta-700 [&_a]:text-marca-700 [&_a]:underline [&_li]:ml-5 [&_li]:list-disc [&_p]:mb-3 [&_strong]:font-semibold"
            dangerouslySetInnerHTML={{ __html: cuerpoSaneado }}
          />
        )}

        {/* --- Secciones propias de la guía --- */}
        {contenido.tipo === 'guia' && (
          <>
            {contenido.personaje && (
              <Seccion titulo="Personaje">
                <p className="text-sm text-tinta-700">{contenido.personaje}</p>
              </Seccion>
            )}

            {contenido.medidas && contenido.medidas.length > 0 && (
              <Seccion titulo="Medidas">
                <dl className="max-w-sm">
                  {contenido.medidas.map((medida) => (
                    <div
                      key={medida.parte}
                      className="flex items-baseline justify-between gap-6 border-b border-tinta-100 py-1.5"
                    >
                      <dt className="text-sm text-tinta-600">{medida.parte}</dt>
                      <dd className="text-sm font-medium text-tinta-900">{medida.valor}</dd>
                    </div>
                  ))}
                </dl>
              </Seccion>
            )}

            {contenido.tecnicas && contenido.tecnicas.length > 0 && (
              <Seccion titulo="Técnicas">
                <Lista elementos={contenido.tecnicas} />
              </Seccion>
            )}

            {contenido.pasos && contenido.pasos.length > 0 && (
              <Seccion titulo="Paso a paso">
                <ol className="space-y-3">
                  {contenido.pasos.map((paso, indice) => (
                    <li key={indice} className="flex gap-3 text-sm leading-relaxed text-tinta-700">
                      <span
                        aria-hidden="true"
                        className="grid size-6 shrink-0 place-items-center rounded-full bg-marca-100 text-xs font-bold text-marca-800"
                      >
                        {indice + 1}
                      </span>
                      {paso}
                    </li>
                  ))}
                </ol>
              </Seccion>
            )}

            {contenido.materiales && contenido.materiales.length > 0 && (
              <Seccion titulo="Materiales">
                <Lista elementos={contenido.materiales} />
              </Seccion>
            )}

            {contenido.presupuesto && (
              <Seccion titulo="Presupuesto declarado">
                <p className="rounded-control bg-acento-50 px-4 py-3 text-sm text-tinta-800">
                  {contenido.presupuesto}
                </p>
                <p className="mt-2 text-xs text-tinta-500">
                  Es una estimación de quien escribió la guía, no un precio de venta.
                </p>
              </Seccion>
            )}

            {contenido.seguridad && (
              <Seccion titulo="Seguridad">
                <p className="rounded-control border-l-4 border-error-600 bg-error-50 px-4 py-3 text-sm leading-relaxed text-tinta-800">
                  {contenido.seguridad}
                </p>
              </Seccion>
            )}
          </>
        )}

        {/* --- Sección propia de la entrevista --- */}
        {contenido.tipo === 'entrevista' &&
          contenido.preguntas &&
          contenido.preguntas.length > 0 && (
            <Seccion titulo="Conversación">
              <dl className="space-y-5">
                {contenido.preguntas.map((pregunta, indice) => (
                  <div key={indice}>
                    <dt className="text-sm font-semibold text-tinta-900">{pregunta}</dt>
                    <dd className="mt-1 border-l-2 border-tinta-200 pl-4 text-sm leading-relaxed text-tinta-700">
                      {contenido.respuestas?.[indice] ?? 'Sin respuesta registrada.'}
                    </dd>
                  </div>
                ))}
              </dl>
            </Seccion>
          )}

        {/* --- Sección propia del artículo --- */}
        {contenido.tipo === 'articulo' && contenido.enlaces && contenido.enlaces.length > 0 && (
          <Seccion titulo="Enlaces">
            <ul className="space-y-2">
              {contenido.enlaces.map((enlace) => (
                <li key={enlace}>
                  <a
                    href={enlace}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="break-all text-sm font-medium text-marca-700 hover:underline"
                  >
                    {enlace}
                  </a>
                </li>
              ))}
            </ul>
          </Seccion>
        )}

        {contenido.video_url && (
          <Seccion titulo="Video">
            <a
              href={contenido.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold text-marca-700 hover:underline"
            >
              Ver el video
              <span className="sr-only"> (se abre en otra pestaña)</span>
            </a>
          </Seccion>
        )}

        <p className="mt-12 border-t border-tinta-200 pt-4 text-xs text-tinta-500">
          Publicado el{' '}
          {contenido.fecha_publicacion
            ? new Date(contenido.fecha_publicacion).toLocaleDateString('es-CL')
            : new Date(contenido.creado_en).toLocaleDateString('es-CL')}
        </p>
      </article>
    </Disposicion>
  )
}
