import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Campo } from '../components/ui/Campo'
import { Etiqueta } from '../components/ui/Etiqueta'
import { Tarjeta } from '../components/ui/Tarjeta'
import {
  ETIQUETAS_TIPO_EVENTO,
  REGIONES_CHILE,
  TIPOS_EVENTO,
  TONO_TIPO_EVENTO,
  formatearFecha,
  mensajeDeFallo,
  modulosApi,
  type PaginaEventos,
} from '../lib/modulos'

const POR_PAGINA = 9

/** Calendario de eventos: filtros en la URL, paginación y carga/error explícitos. */
export function EventosPagina() {
  const [parametros, setParametros] = useSearchParams()
  const [datos, setDatos] = useState<PaginaEventos | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [reintento, setReintento] = useState(0)

  const q = parametros.get('q') ?? ''
  const tipo = parametros.get('tipo') ?? ''
  const region = parametros.get('region') ?? ''
  const pagina = Math.max(1, Number(parametros.get('pagina') ?? '1') || 1)

  // La query armada como cadena es la clave del efecto: dos renders con los
  // mismos filtros no disparan dos peticiones iguales.
  const consulta = useMemo(() => {
    const busqueda = new URLSearchParams()
    if (q) busqueda.set('q', q)
    if (tipo) busqueda.set('tipo', tipo)
    if (region) busqueda.set('region', region)
    busqueda.set('limite', String(POR_PAGINA))
    busqueda.set('desplazamiento', String((pagina - 1) * POR_PAGINA))
    return busqueda.toString()
  }, [q, tipo, region, pagina])

  useEffect(() => {
    let vigente = true
    // El reinicio va en microtarea para no provocar un render en cascada
    // dentro del effect (regla de React Compiler).
    queueMicrotask(() => {
      if (!vigente) return
      setCargando(true)
      setError('')
      modulosApi
        .eventos(consulta)
        .then((paginaDatos) => {
          if (!vigente) return
          setDatos(paginaDatos)
          setCargando(false)
        })
        .catch((fallo: unknown) => {
          if (!vigente) return
          setError(mensajeDeFallo(fallo, 'No pudimos cargar los eventos. Revisa tu conexión.'))
          setCargando(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [consulta, reintento])

  function cambiarFiltros(cambios: Record<string, string | null>) {
    const siguiente = new URLSearchParams(parametros)
    for (const [clave, valor] of Object.entries(cambios)) {
      if (valor === null || valor === '') siguiente.delete(clave)
      else siguiente.set(clave, valor)
    }
    // Cambiar un filtro vuelve a la primera página: si no, se pediría una
    // página que quizás ya no existe con el nuevo conjunto de resultados.
    siguiente.delete('pagina')
    setParametros(siguiente)
  }

  function irAPagina(numero: number) {
    const siguiente = new URLSearchParams(parametros)
    if (numero <= 1) siguiente.delete('pagina')
    else siguiente.set('pagina', String(numero))
    setParametros(siguiente)
  }

  const totalPaginas = datos ? Math.max(1, Math.ceil(datos.total / POR_PAGINA)) : 1
  const hayFiltros = Boolean(q || tipo || region)

  return (
    <Disposicion>
      <div className="mx-auto max-w-6xl px-4 py-12">
        <header className="max-w-2xl">
          <h1 className="text-3xl font-black tracking-tight text-tinta-900">
            Calendario de eventos
          </h1>
          <p className="mt-3 text-base text-tinta-600">
            Convenciones, concursos, ferias y talleres de la comunidad cosplay
            chilena. Busca por nombre, tipo o región y revisa quién va.
          </p>
        </header>

        <section
          aria-labelledby="titulo-filtros-eventos"
          className="mt-8 rounded-tarjeta border border-tinta-200 bg-white p-5"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 id="titulo-filtros-eventos" className="text-sm font-semibold text-tinta-900">
              Filtrar eventos
            </h2>
            {hayFiltros && (
              <Boton
                variante="fantasma"
                tamano="sm"
                onClick={() => setParametros(new URLSearchParams())}
              >
                Limpiar filtros
              </Boton>
            )}
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Campo
              etiqueta="Buscar"
              id="filtro-q-eventos"
              type="search"
              placeholder="Nombre del evento"
              value={q}
              onChange={(evento) => cambiarFiltros({ q: evento.target.value || null })}
            />

            <div className="flex flex-col gap-1.5">
              <label htmlFor="filtro-tipo-eventos" className="text-sm font-medium text-tinta-800">
                Tipo de evento
              </label>
              <select
                id="filtro-tipo-eventos"
                value={tipo}
                onChange={(evento) => cambiarFiltros({ tipo: evento.target.value || null })}
                className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
              >
                <option value="">Todos los tipos</option>
                {TIPOS_EVENTO.map((valor) => (
                  <option key={valor} value={valor}>
                    {ETIQUETAS_TIPO_EVENTO[valor]}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="filtro-region-eventos" className="text-sm font-medium text-tinta-800">
                Región
              </label>
              <select
                id="filtro-region-eventos"
                value={region}
                onChange={(evento) => cambiarFiltros({ region: evento.target.value || null })}
                className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
              >
                <option value="">Todas las regiones</option>
                {REGIONES_CHILE.map((nombre) => (
                  <option key={nombre} value={nombre}>
                    {nombre}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        <p aria-live="polite" className="mt-6 text-sm text-tinta-600">
          {cargando
            ? datos
              ? 'Actualizando eventos…'
              : 'Cargando eventos…'
            : datos
              ? datos.total === 1
                ? '1 evento encontrado'
                : `${datos.total} eventos encontrados`
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

        {!cargando && !error && datos && datos.total === 0 && (
          <div className="mt-8 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-16 text-center">
            <p className="text-base font-semibold text-tinta-900">
              No hay eventos con esos filtros
            </p>
            <p className="mx-auto mt-2 max-w-md text-sm text-tinta-600">
              Prueba con otra región, otro tipo o quita los filtros para ver el
              calendario completo.
            </p>
            {hayFiltros && (
              <div className="mt-6 flex justify-center">
                <Boton variante="secundario" onClick={() => setParametros(new URLSearchParams())}>
                  Quitar los filtros
                </Boton>
              </div>
            )}
          </div>
        )}

        {datos && datos.total > 0 && (
          <>
            <ul className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {datos.elementos.map((evento) => {
                const enlace = `/eventos/${encodeURIComponent(evento.id_evento)}`
                return (
                  <Tarjeta como="li" key={evento.id_evento} className="flex h-full flex-col gap-3">
                    <div className="flex items-start justify-between gap-2">
                      <Etiqueta tono={TONO_TIPO_EVENTO[evento.tipo] ?? 'neutro'}>
                        {ETIQUETAS_TIPO_EVENTO[evento.tipo] ?? evento.tipo}
                      </Etiqueta>
                      <span className="text-xs font-medium text-tinta-500">
                        {evento.total_participantes === 1
                          ? '1 inscrito'
                          : `${evento.total_participantes} inscritos`}
                      </span>
                    </div>

                    <h2 className="text-base font-semibold leading-snug text-tinta-900">
                      <Link to={enlace} className="hover:text-marca-700 hover:underline">
                        {evento.nombre}
                      </Link>
                    </h2>

                    <dl className="flex-1 space-y-1 text-sm text-tinta-600">
                      <div>
                        <dt className="sr-only">Fecha</dt>
                        <dd>{formatearFecha(evento.fecha_inicio)}</dd>
                      </div>
                      {evento.fecha_fin && (
                        <div>
                          <dt className="sr-only">Hasta</dt>
                          <dd>hasta el {formatearFecha(evento.fecha_fin)}</dd>
                        </div>
                      )}
                      <div>
                        <dt className="sr-only">Lugar</dt>
                        <dd>
                          {evento.lugar}
                          {evento.region ? ` · ${evento.region}` : ''}
                        </dd>
                      </div>
                    </dl>

                    <Link
                      to={enlace}
                      className="mt-auto text-sm font-semibold text-marca-700 hover:underline"
                    >
                      Ver detalle
                      <span aria-hidden="true"> →</span>
                    </Link>
                  </Tarjeta>
                )
              })}
            </ul>

            {totalPaginas > 1 && (
              <nav
                aria-label="Paginación de eventos"
                className="mt-10 flex items-center justify-between gap-4"
              >
                <Boton
                  variante="secundario"
                  onClick={() => irAPagina(pagina - 1)}
                  disabled={pagina <= 1}
                >
                  Anterior
                </Boton>
                <p className="text-sm text-tinta-600">
                  Página {pagina} de {totalPaginas}
                </p>
                <Boton
                  variante="secundario"
                  onClick={() => irAPagina(pagina + 1)}
                  disabled={pagina >= totalPaginas}
                >
                  Siguiente
                </Boton>
              </nav>
            )}
          </>
        )}
      </div>
    </Disposicion>
  )
}
