import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Campo } from '../components/ui/Campo'
import { Etiqueta } from '../components/ui/Etiqueta'
import { Tarjeta } from '../components/ui/Tarjeta'
import {
  ETIQUETAS_PLATAFORMA,
  ETIQUETAS_TIPO_TIENDA,
  PLATAFORMAS,
  REGIONES_CHILE,
  TIPOS_TIENDA,
  enlaceExterno,
  mensajeDeFallo,
  modulosApi,
  type PaginaGrupos,
  type PaginaTiendas,
} from '../lib/modulos'

const LIMITE_TIENDAS = 12
const LIMITE_GRUPOS = 12

/** «Dónde comprar» y grupos de la comunidad, con acceso al foro y desafíos. */
export function ComunidadPagina() {
  // --- Filtros de tiendas ------------------------------------------------
  const [qTiendas, setQTiendas] = useState('')
  const [tipo, setTipo] = useState('')
  const [regionTiendas, setRegionTiendas] = useState('')

  const [tiendas, setTiendas] = useState<PaginaTiendas | null>(null)
  const [cargandoTiendas, setCargandoTiendas] = useState(true)
  const [errorTiendas, setErrorTiendas] = useState('')
  const [reintentoTiendas, setReintentoTiendas] = useState(0)

  // --- Filtros de grupos -------------------------------------------------
  const [regionGrupos, setRegionGrupos] = useState('')
  const [plataforma, setPlataforma] = useState('')

  const [grupos, setGrupos] = useState<PaginaGrupos | null>(null)
  const [cargandoGrupos, setCargandoGrupos] = useState(true)
  const [errorGrupos, setErrorGrupos] = useState('')
  const [reintentoGrupos, setReintentoGrupos] = useState(0)

  const consultaTiendas = useMemo(() => {
    const busqueda = new URLSearchParams()
    if (qTiendas) busqueda.set('q', qTiendas)
    if (tipo) busqueda.set('tipo', tipo)
    if (regionTiendas) busqueda.set('region', regionTiendas)
    busqueda.set('limite', String(LIMITE_TIENDAS))
    return busqueda.toString()
  }, [qTiendas, tipo, regionTiendas])

  const consultaGrupos = useMemo(() => {
    const busqueda = new URLSearchParams()
    if (regionGrupos) busqueda.set('region', regionGrupos)
    if (plataforma) busqueda.set('plataforma', plataforma)
    busqueda.set('limite', String(LIMITE_GRUPOS))
    return busqueda.toString()
  }, [regionGrupos, plataforma])

  useEffect(() => {
    let vigente = true
    // El reinicio va en microtarea para no provocar un render en cascada
    // dentro del effect (regla de React Compiler).
    queueMicrotask(() => {
      if (!vigente) return
      setCargandoTiendas(true)
      setErrorTiendas('')
      modulosApi
        .tiendas(consultaTiendas)
        .then((datos) => {
          if (!vigente) return
          setTiendas(datos)
          setCargandoTiendas(false)
        })
        .catch((fallo: unknown) => {
          if (!vigente) return
          setErrorTiendas(mensajeDeFallo(fallo, 'No pudimos cargar las tiendas. Revisa tu conexión.'))
          setCargandoTiendas(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [consultaTiendas, reintentoTiendas])

  useEffect(() => {
    let vigente = true
    // El reinicio va en microtarea para no provocar un render en cascada
    // dentro del effect (regla de React Compiler).
    queueMicrotask(() => {
      if (!vigente) return
      setCargandoGrupos(true)
      setErrorGrupos('')
      modulosApi
        .grupos(consultaGrupos)
        .then((datos) => {
          if (!vigente) return
          setGrupos(datos)
          setCargandoGrupos(false)
        })
        .catch((fallo: unknown) => {
          if (!vigente) return
          setErrorGrupos(mensajeDeFallo(fallo, 'No pudimos cargar los grupos. Revisa tu conexión.'))
          setCargandoGrupos(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [consultaGrupos, reintentoGrupos])

  const hayFiltrosTiendas = Boolean(qTiendas || tipo || regionTiendas)
  const hayFiltrosGrupos = Boolean(regionGrupos || plataforma)

  return (
    <Disposicion>
      <div className="mx-auto max-w-6xl px-4 py-12">
        <header className="max-w-2xl">
          <h1 className="text-3xl font-black tracking-tight text-tinta-900">
            Comunidad
          </h1>
          <p className="mt-3 text-base text-tinta-600">
            Dónde comprar materiales en Chile y dónde se junta la comunidad
            fuera de la plataforma. Para conversar y participar, también están
            el foro y los desafíos mensuales.
          </p>
        </header>

        <nav aria-label="Otros espacios de la comunidad" className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/foro"
            className="rounded-control border border-tinta-300 bg-white px-4 py-2 text-sm font-semibold text-tinta-800 hover:bg-tinta-100"
          >
            Ir al foro
          </Link>
          <Link
            to="/desafios"
            className="rounded-control border border-tinta-300 bg-white px-4 py-2 text-sm font-semibold text-tinta-800 hover:bg-tinta-100"
          >
            Ver desafíos mensuales
          </Link>
          <Link
            to="/eventos"
            className="rounded-control border border-tinta-300 bg-white px-4 py-2 text-sm font-semibold text-tinta-800 hover:bg-tinta-100"
          >
            Calendario de eventos
          </Link>
        </nav>

        {/* --- Dónde comprar -------------------------------------------- */}
        <section aria-labelledby="titulo-tiendas" className="mt-12">
          <h2 id="titulo-tiendas" className="text-2xl font-bold tracking-tight text-tinta-900">
            Dónde comprar
          </h2>
          <p className="mt-2 text-sm text-tinta-600">
            Telas, insumos, pelucas e impresión 3D. Fíjate si envían a Chile.
          </p>

          <div className="mt-6 rounded-tarjeta border border-tinta-200 bg-white p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-tinta-900">Filtrar tiendas</h3>
              {hayFiltrosTiendas && (
                <Boton
                  variante="fantasma"
                  tamano="sm"
                  onClick={() => {
                    setQTiendas('')
                    setTipo('')
                    setRegionTiendas('')
                  }}
                >
                  Limpiar filtros
                </Boton>
              )}
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Campo
                etiqueta="Buscar"
                id="filtro-q-tiendas"
                type="search"
                placeholder="Nombre de la tienda"
                value={qTiendas}
                onChange={(evento) => setQTiendas(evento.target.value)}
              />

              <div className="flex flex-col gap-1.5">
                <label htmlFor="filtro-tipo-tiendas" className="text-sm font-medium text-tinta-800">
                  Tipo de tienda
                </label>
                <select
                  id="filtro-tipo-tiendas"
                  value={tipo}
                  onChange={(evento) => setTipo(evento.target.value)}
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                >
                  <option value="">Todos los tipos</option>
                  {TIPOS_TIENDA.map((valor) => (
                    <option key={valor} value={valor}>
                      {ETIQUETAS_TIPO_TIENDA[valor]}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="filtro-region-tiendas" className="text-sm font-medium text-tinta-800">
                  Región
                </label>
                <select
                  id="filtro-region-tiendas"
                  value={regionTiendas}
                  onChange={(evento) => setRegionTiendas(evento.target.value)}
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
          </div>

          <p aria-live="polite" className="mt-5 text-sm text-tinta-600">
            {cargandoTiendas
              ? tiendas
                ? 'Actualizando tiendas…'
                : 'Cargando tiendas…'
              : tiendas
                ? tiendas.total === 1
                  ? '1 tienda encontrada'
                  : `${tiendas.total} tiendas encontradas`
                : ''}
          </p>

          {errorTiendas && (
            <div role="alert" className="mt-4 rounded-control bg-error-50 px-3 py-3 text-sm text-error-600">
              <p className="font-medium">{errorTiendas}</p>
              <div className="mt-3">
                <Boton
                  variante="secundario"
                  tamano="sm"
                  onClick={() => setReintentoTiendas((valor) => valor + 1)}
                >
                  Reintentar
                </Boton>
              </div>
            </div>
          )}

          {!cargandoTiendas && !errorTiendas && tiendas && tiendas.total === 0 && (
            <div className="mt-4 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-10 text-center">
              <p className="text-sm font-semibold text-tinta-900">
                No encontramos tiendas con esos filtros
              </p>
              <p className="mt-2 text-sm text-tinta-600">
                Prueba con otro tipo o quita los filtros para ver el listado completo.
              </p>
            </div>
          )}

          {tiendas && tiendas.total > 0 && (
            <ul className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {tiendas.elementos.map((tienda) => {
                const enlace = enlaceExterno(tienda.enlace_web)
                return (
                  <Tarjeta como="li" key={tienda.id_tienda} className="flex h-full flex-col gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Etiqueta tono="marca">
                        {ETIQUETAS_TIPO_TIENDA[tienda.tipo] ?? tienda.tipo}
                      </Etiqueta>
                      <Etiqueta tono={tienda.envia_a_chile ? 'exito' : 'neutro'}>
                        {tienda.envia_a_chile ? 'Envía a Chile' : 'Solo local'}
                      </Etiqueta>
                    </div>

                    <h3 className="text-base font-semibold text-tinta-900">{tienda.nombre}</h3>
                    <p className="flex-1 text-sm text-tinta-600">
                      {tienda.region ? `Región ${tienda.region}` : 'Sin región declarada'}
                    </p>

                    {enlace ? (
                      <a
                        href={enlace}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-auto text-sm font-semibold text-marca-700 hover:underline"
                      >
                        Visitar tienda <span aria-hidden="true">↗</span>
                      </a>
                    ) : (
                      <p className="mt-auto text-xs text-tinta-500">Sin enlace publicado</p>
                    )}
                  </Tarjeta>
                )
              })}
            </ul>
          )}
        </section>

        {/* --- Grupos ---------------------------------------------------- */}
        <section aria-labelledby="titulo-grupos" className="mt-16">
          <h2 id="titulo-grupos" className="text-2xl font-bold tracking-tight text-tinta-900">
            Grupos de la comunidad
          </h2>
          <p className="mt-2 text-sm text-tinta-600">
            Servidores, grupos y foros donde se organizan quedatadas, ferias y
            dudas de último minuto.
          </p>

          <div className="mt-6 rounded-tarjeta border border-tinta-200 bg-white p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-tinta-900">Filtrar grupos</h3>
              {hayFiltrosGrupos && (
                <Boton
                  variante="fantasma"
                  tamano="sm"
                  onClick={() => {
                    setRegionGrupos('')
                    setPlataforma('')
                  }}
                >
                  Limpiar filtros
                </Boton>
              )}
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="filtro-region-grupos" className="text-sm font-medium text-tinta-800">
                  Región
                </label>
                <select
                  id="filtro-region-grupos"
                  value={regionGrupos}
                  onChange={(evento) => setRegionGrupos(evento.target.value)}
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

              <div className="flex flex-col gap-1.5">
                <label htmlFor="filtro-plataforma-grupos" className="text-sm font-medium text-tinta-800">
                  Plataforma
                </label>
                <select
                  id="filtro-plataforma-grupos"
                  value={plataforma}
                  onChange={(evento) => setPlataforma(evento.target.value)}
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                >
                  <option value="">Todas las plataformas</option>
                  {PLATAFORMAS.map((valor) => (
                    <option key={valor} value={valor}>
                      {ETIQUETAS_PLATAFORMA[valor]}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <p aria-live="polite" className="mt-5 text-sm text-tinta-600">
            {cargandoGrupos
              ? grupos
                ? 'Actualizando grupos…'
                : 'Cargando grupos…'
              : grupos
                ? grupos.total === 1
                  ? '1 grupo encontrado'
                  : `${grupos.total} grupos encontrados`
                : ''}
          </p>

          {errorGrupos && (
            <div role="alert" className="mt-4 rounded-control bg-error-50 px-3 py-3 text-sm text-error-600">
              <p className="font-medium">{errorGrupos}</p>
              <div className="mt-3">
                <Boton
                  variante="secundario"
                  tamano="sm"
                  onClick={() => setReintentoGrupos((valor) => valor + 1)}
                >
                  Reintentar
                </Boton>
              </div>
            </div>
          )}

          {!cargandoGrupos && !errorGrupos && grupos && grupos.total === 0 && (
            <div className="mt-4 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-10 text-center">
              <p className="text-sm font-semibold text-tinta-900">
                No encontramos grupos con esos filtros
              </p>
              <p className="mt-2 text-sm text-tinta-600">
                Prueba con otra plataforma o mira todos los grupos disponibles.
              </p>
            </div>
          )}

          {grupos && grupos.total > 0 && (
            <ul className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {grupos.elementos.map((grupo) => {
                const enlace = enlaceExterno(grupo.enlace)
                return (
                  <Tarjeta como="li" key={grupo.id_comunidad} className="flex h-full flex-col gap-3">
                    <Etiqueta tono="acento">
                      {ETIQUETAS_PLATAFORMA[grupo.plataforma] ?? grupo.plataforma}
                    </Etiqueta>
                    <h3 className="text-base font-semibold text-tinta-900">{grupo.nombre}</h3>
                    <p className="flex-1 text-sm text-tinta-600">
                      {grupo.region ? `Región ${grupo.region}` : 'Grupo nacional'}
                    </p>
                    {enlace ? (
                      <a
                        href={enlace}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-auto text-sm font-semibold text-marca-700 hover:underline"
                      >
                        Unirme al grupo <span aria-hidden="true">↗</span>
                      </a>
                    ) : (
                      <p className="mt-auto text-xs text-tinta-500">Sin enlace publicado</p>
                    )}
                  </Tarjeta>
                )
              })}
            </ul>
          )}
        </section>
      </div>
    </Disposicion>
  )
}
