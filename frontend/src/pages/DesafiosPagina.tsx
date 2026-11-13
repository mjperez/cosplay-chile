import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Etiqueta } from '../components/ui/Etiqueta'
import { Tarjeta } from '../components/ui/Tarjeta'
import {
  formatearFecha,
  formatearMes,
  mensajeDeFallo,
  modulosApi,
  type Desafio,
  type PaginaDesafios,
} from '../lib/modulos'

interface DatosPagina {
  vigente: Desafio | null
  historial: PaginaDesafios
}

/** Desafío del mes en grande y el historial de convocatorias anteriores. */
export function DesafiosPagina() {
  const [datos, setDatos] = useState<DatosPagina | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [reintento, setReintento] = useState(0)

  useEffect(() => {
    let vigente = true
    // El reinicio va en una microtarea: un setState sincrónico dentro del
    // effect provoca un render en cascada (regla de React Compiler). La
    // petición sale en el mismo turno, así que no hay parpadeo visible.
    queueMicrotask(() => {
      if (!vigente) return
      setCargando(true)
      setError('')
      Promise.all([modulosApi.desafioVigente(), modulosApi.desafios()])
        .then(([desafioVigente, historial]) => {
          if (!vigente) return
          setDatos({ vigente: desafioVigente, historial })
          setCargando(false)
        })
        .catch((fallo: unknown) => {
          if (!vigente) return
          setError(mensajeDeFallo(fallo, 'No pudimos cargar los desafíos. Revisa tu conexión.'))
          setCargando(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [reintento])

  const destacado = datos?.vigente ?? null
  const historial = datos?.historial ?? null

  return (
    <Disposicion>
      <div className="mx-auto max-w-4xl px-4 py-12">
        <header className="max-w-2xl">
          <h1 className="text-3xl font-black tracking-tight text-tinta-900">
            Desafíos mensuales
          </h1>
          <p className="mt-3 text-base text-tinta-600">
            Cada mes proponemos un tema para crear, aprender y mostrar el
            proceso. Participa desde el foro y comparte tus avances.
          </p>
        </header>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/foro"
            className="rounded-control border border-tinta-300 bg-white px-4 py-2 text-sm font-semibold text-tinta-800 hover:bg-tinta-100"
          >
            Conversar en el foro
          </Link>
          <Link
            to="/comunidad"
            className="rounded-control border border-tinta-300 bg-white px-4 py-2 text-sm font-semibold text-tinta-800 hover:bg-tinta-100"
          >
            Tiendas y grupos
          </Link>
        </div>

        <p aria-live="polite" className="mt-8 text-sm text-tinta-600">
          {cargando
            ? datos
              ? 'Actualizando desafíos…'
              : 'Cargando desafíos…'
            : ''}
        </p>

        {error && (
          <div role="alert" className="mt-4 rounded-control bg-error-50 px-3 py-3 text-sm text-error-600">
            <p className="font-medium">{error}</p>
            <div className="mt-3">
              <Boton
                variante="secundario"
                tamano="sm"
                onClick={() => setReintento((valor) => valor + 1)}
              >
                Reintentar
              </Boton>
            </div>
          </div>
        )}

        {/* Si una recarga falla, se conserva el último historial en pantalla. */}
        {datos && historial && (
          <>
            <section aria-labelledby="titulo-vigente" className="mt-6">
              <h2 id="titulo-vigente" className="text-xl font-bold text-tinta-900">
                Desafío vigente
              </h2>

              {destacado ? (
                <Tarjeta como="article" className="mt-4 border-marca-200 bg-marca-50">
                  <div className="flex flex-wrap items-center gap-2">
                    <Etiqueta tono="marca">{formatearMes(destacado.mes)}</Etiqueta>
                    {destacado.nombre_ganador && (
                      <Etiqueta tono="exito">Ganador: {destacado.nombre_ganador}</Etiqueta>
                    )}
                  </div>

                  <h3 className="mt-4 text-2xl font-black tracking-tight text-tinta-900">
                    {destacado.titulo}
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-tinta-600">
                    ¿Te animas? Publica tu proceso, tus dudas y el resultado final
                    en el foro para que la comunidad lo vea.
                  </p>
                  <p className="mt-4 text-xs text-tinta-500">
                    Convocatoria abierta el {formatearFecha(destacado.creado_en)}
                  </p>
                  <div className="mt-6">
                    <Link
                      to="/foro"
                      className="inline-flex items-center rounded-control bg-marca-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-marca-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                    >
                      Ir al foro
                      <span aria-hidden="true"> →</span>
                    </Link>
                  </div>
                </Tarjeta>
              ) : (
                <div className="mt-4 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-12 text-center">
                  <p className="text-base font-semibold text-tinta-900">
                    No hay un desafío vigente por ahora
                  </p>
                  <p className="mx-auto mt-2 max-w-md text-sm text-tinta-600">
                    Vuelve a mirar en unos días: las convocatorias se publican
                    al comienzo de cada mes. Mientras tanto, el foro sigue abierto.
                  </p>
                </div>
              )}
            </section>

            <section aria-labelledby="titulo-historial" className="mt-12">
              <h2 id="titulo-historial" className="text-xl font-bold text-tinta-900">
                Historial ({historial.total})
              </h2>

              {historial.total === 0 ? (
                <div className="mt-4 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-10 text-center">
                  <p className="text-sm font-semibold text-tinta-900">
                    Todavía no hay desafíos registrados
                  </p>
                  <p className="mt-2 text-sm text-tinta-600">
                    Cuando se publique el primero, va a aparecer en esta lista.
                  </p>
                </div>
              ) : (
                <ul className="mt-4 flex flex-col gap-3">
                  {historial.elementos.map((desafio) => {
                    const esVigente = destacado?.id_desafio === desafio.id_desafio
                    return (
                      <Tarjeta
                        como="li"
                        key={desafio.id_desafio}
                        className="flex flex-wrap items-center justify-between gap-3"
                      >
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <Etiqueta tono={esVigente ? 'marca' : 'neutro'}>
                              {formatearMes(desafio.mes)}
                            </Etiqueta>
                            {esVigente && <Etiqueta tono="acento">Vigente</Etiqueta>}
                          </div>
                          <h3 className="mt-2 text-base font-semibold text-tinta-900">
                            {desafio.titulo}
                          </h3>
                          <p className="mt-1 text-xs text-tinta-500">
                            Publicado el {formatearFecha(desafio.creado_en)}
                          </p>
                        </div>
                        <div className="text-sm">
                          {desafio.nombre_ganador ? (
                            <p className="font-medium text-exito-600">
                              Ganó {desafio.nombre_ganador}
                            </p>
                          ) : (
                            <p className="text-tinta-500">Sin ganador aún</p>
                          )}
                        </div>
                      </Tarjeta>
                    )
                  })}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </Disposicion>
  )
}
