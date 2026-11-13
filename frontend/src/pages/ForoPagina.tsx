import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Campo } from '../components/ui/Campo'
import { Etiqueta } from '../components/ui/Etiqueta'
import { Tarjeta } from '../components/ui/Tarjeta'
import { ErrorApi } from '../lib/api'
import { useAuth } from '../lib/contextoAuth'
import {
  CATEGORIAS_FORO,
  formatearFecha,
  mensajeDeFallo,
  modulosApi,
  type PaginaTemas,
} from '../lib/modulos'

const POR_PAGINA = 10

/** Listado de temas del foro con filtros y formulario de tema nuevo. */
export function ForoPagina() {
  const [parametros, setParametros] = useSearchParams()
  const navegar = useNavigate()
  const { usuario, cargando: cargandoAuth } = useAuth()

  const [datos, setDatos] = useState<PaginaTemas | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [reintento, setReintento] = useState(0)

  const [titulo, setTitulo] = useState('')
  const [categoria, setCategoria] = useState(CATEGORIAS_FORO[0])
  const [contenido, setContenido] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [errorFormulario, setErrorFormulario] = useState('')

  const q = parametros.get('q') ?? ''
  const categoriaFiltro = parametros.get('categoria') ?? ''
  const pagina = Math.max(1, Number(parametros.get('pagina') ?? '1') || 1)

  const consulta = useMemo(() => {
    const busqueda = new URLSearchParams()
    if (q) busqueda.set('q', q)
    if (categoriaFiltro) busqueda.set('categoria', categoriaFiltro)
    busqueda.set('limite', String(POR_PAGINA))
    busqueda.set('desplazamiento', String((pagina - 1) * POR_PAGINA))
    return busqueda.toString()
  }, [q, categoriaFiltro, pagina])

  useEffect(() => {
    let vigente = true
    // El reinicio va en microtarea para no provocar un render en cascada
    // dentro del effect (regla de React Compiler).
    queueMicrotask(() => {
      if (!vigente) return
      setCargando(true)
      setError('')
      modulosApi
        .temas(consulta)
        .then((paginaDatos) => {
          if (!vigente) return
          setDatos(paginaDatos)
          setCargando(false)
        })
        .catch((fallo: unknown) => {
          if (!vigente) return
          setError(mensajeDeFallo(fallo, 'No pudimos cargar los temas del foro. Revisa tu conexión.'))
          setCargando(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [consulta, reintento])

  // El backend acepta categorías libres: además de las conocidas se ofrecen
  // las que aparezcan en los temas ya cargados.
  const categorias = useMemo(() => {
    const conjunto = new Set<string>(CATEGORIAS_FORO)
    for (const tema of datos?.elementos ?? []) {
      if (tema.categoria) conjunto.add(tema.categoria)
    }
    return Array.from(conjunto)
  }, [datos])

  function cambiarFiltros(cambios: Record<string, string | null>) {
    const siguiente = new URLSearchParams(parametros)
    for (const [clave, valor] of Object.entries(cambios)) {
      if (valor === null || valor === '') siguiente.delete(clave)
      else siguiente.set(clave, valor)
    }
    siguiente.delete('pagina')
    setParametros(siguiente)
  }

  function irAPagina(numero: number) {
    const siguiente = new URLSearchParams(parametros)
    if (numero <= 1) siguiente.delete('pagina')
    else siguiente.set('pagina', String(numero))
    setParametros(siguiente)
  }

  async function crearTema(formulario: FormEvent) {
    formulario.preventDefault()
    setErrorFormulario('')

    const tituloLimpio = titulo.trim()
    const contenidoLimpio = contenido.trim()
    if (tituloLimpio.length < 3) {
      setErrorFormulario('El título tiene que tener al menos 3 caracteres.')
      return
    }
    if (contenidoLimpio.length < 5) {
      setErrorFormulario('Escribe un poco más: el contenido necesita al menos 5 caracteres.')
      return
    }

    setEnviando(true)
    try {
      const creado = await modulosApi.crearTema({
        titulo: tituloLimpio,
        categoria,
        contenido: contenidoLimpio,
      })
      navegar(`/foro/${encodeURIComponent(creado.id_tema)}`)
    } catch (fallo: unknown) {
      if (fallo instanceof ErrorApi && fallo.estado === 401) {
        setErrorFormulario('Tu sesión venció. Vuelve a ingresar para publicar un tema.')
      } else if (fallo instanceof ErrorApi && fallo.estado === 403) {
        setErrorFormulario('Tu cuenta no puede publicar temas en el foro.')
      } else {
        setErrorFormulario(mensajeDeFallo(fallo, 'No pudimos publicar el tema. Revisa tu conexión.'))
      }
    } finally {
      setEnviando(false)
    }
  }

  const totalPaginas = datos ? Math.max(1, Math.ceil(datos.total / POR_PAGINA)) : 1
  const hayFiltros = Boolean(q || categoriaFiltro)

  return (
    <Disposicion>
      <div className="mx-auto max-w-5xl px-4 py-12">
        <header className="max-w-2xl">
          <h1 className="text-3xl font-black tracking-tight text-tinta-900">Foro</h1>
          <p className="mt-3 text-base text-tinta-600">
            Preguntas, tutoriales y conversaciones de la comunidad. Si algo te
            sirvió, déjalo escrito acá para quien viene llegando.
          </p>
        </header>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/desafios"
            className="rounded-control border border-tinta-300 bg-white px-4 py-2 text-sm font-semibold text-tinta-800 hover:bg-tinta-100"
          >
            Ver desafíos mensuales
          </Link>
          <Link
            to="/comunidad"
            className="rounded-control border border-tinta-300 bg-white px-4 py-2 text-sm font-semibold text-tinta-800 hover:bg-tinta-100"
          >
            Tiendas y grupos
          </Link>
        </div>

        <section
          aria-labelledby="titulo-filtros-foro"
          className="mt-8 rounded-tarjeta border border-tinta-200 bg-white p-5"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 id="titulo-filtros-foro" className="text-sm font-semibold text-tinta-900">
              Filtrar temas
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

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <Campo
              etiqueta="Buscar"
              id="filtro-q-foro"
              type="search"
              placeholder="Título o contenido"
              value={q}
              onChange={(evento) => cambiarFiltros({ q: evento.target.value || null })}
            />

            <div className="flex flex-col gap-1.5">
              <label htmlFor="filtro-categoria-foro" className="text-sm font-medium text-tinta-800">
                Categoría
              </label>
              <select
                id="filtro-categoria-foro"
                value={categoriaFiltro}
                onChange={(evento) =>
                  cambiarFiltros({ categoria: evento.target.value || null })
                }
                className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
              >
                <option value="">Todas las categorías</option>
                {categorias.map((nombre) => (
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
              ? 'Actualizando temas…'
              : 'Cargando temas…'
            : datos
              ? datos.total === 1
                ? '1 tema encontrado'
                : `${datos.total} temas encontrados`
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
              No hay temas con esos filtros
            </p>
            <p className="mx-auto mt-2 max-w-md text-sm text-tinta-600">
              Prueba con otra búsqueda o abre el primer tema de esta categoría.
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
            <ul className="mt-6 grid gap-4">
              {datos.elementos.map((tema) => {
                const enlace = `/foro/${encodeURIComponent(tema.id_tema)}`
                return (
                  <Tarjeta como="li" key={tema.id_tema} className="flex flex-col gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Etiqueta tono="marca">{tema.categoria}</Etiqueta>
                      {tema.estado === 'cerrado' && (
                        <Etiqueta tono="neutro">Cerrado</Etiqueta>
                      )}
                      <span className="text-xs text-tinta-500">
                        {tema.total_respuestas === 1
                          ? '1 respuesta'
                          : `${tema.total_respuestas} respuestas`}
                      </span>
                    </div>

                    <h2 className="text-lg font-semibold leading-snug text-tinta-900">
                      <Link to={enlace} className="hover:text-marca-700 hover:underline">
                        {tema.titulo}
                      </Link>
                    </h2>

                    {tema.contenido && (
                      <p className="line-clamp-2 text-sm leading-relaxed text-tinta-600">
                        {tema.contenido}
                      </p>
                    )}

                    <p className="text-xs text-tinta-500">
                      Por {tema.nombre_autor} · {formatearFecha(tema.creado_en)}
                    </p>

                    <Link
                      to={enlace}
                      className="text-sm font-semibold text-marca-700 hover:underline"
                    >
                      Leer la conversación
                      <span aria-hidden="true"> →</span>
                    </Link>
                  </Tarjeta>
                )
              })}
            </ul>

            {totalPaginas > 1 && (
              <nav
                aria-label="Paginación del foro"
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

        {/* --- Nuevo tema ------------------------------------------------ */}
        <section aria-labelledby="titulo-nuevo-tema" className="mt-12">
          <Tarjeta>
            <h2 id="titulo-nuevo-tema" className="text-lg font-bold text-tinta-900">
              Nuevo tema
            </h2>

            {cargandoAuth ? (
              <p aria-live="polite" className="mt-3 text-sm text-tinta-600">
                Revisando tu sesión…
              </p>
            ) : !usuario ? (
              <p className="mt-3 text-sm leading-relaxed text-tinta-600">
                Para abrir una conversación tienes que{' '}
                <Link
                  to="/ingresar"
                  state={{ desde: '/foro' }}
                  className="font-semibold text-marca-700 hover:underline"
                >
                  ingresar
                </Link>
                . Leer el foro es abierto para todos.
              </p>
            ) : (
              <form onSubmit={crearTema} className="mt-5 flex flex-col gap-4" noValidate>
                <Campo
                  etiqueta="Título"
                  id="campo-titulo-nuevo-tema"
                  required
                  minLength={3}
                  maxLength={200}
                  value={titulo}
                  onChange={(evento) => setTitulo(evento.target.value)}
                />

                <div className="flex flex-col gap-1.5">
                  <label htmlFor="categoria-nuevo-tema" className="text-sm font-medium text-tinta-800">
                    Categoría
                  </label>
                  <select
                    id="categoria-nuevo-tema"
                    value={categoria}
                    onChange={(evento) => setCategoria(evento.target.value)}
                    className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                  >
                    {categorias.map((nombre) => (
                      <option key={nombre} value={nombre}>
                        {nombre}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label htmlFor="contenido-nuevo-tema" className="text-sm font-medium text-tinta-800">
                    Contenido
                  </label>
                  <textarea
                    id="contenido-nuevo-tema"
                    rows={5}
                    required
                    minLength={5}
                    maxLength={20000}
                    value={contenido}
                    onChange={(evento) => setContenido(evento.target.value)}
                    placeholder="Cuenta tu duda, comparte el paso a paso o muestra tu avance."
                    className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 placeholder:text-tinta-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                  />
                  <p className="text-xs text-tinta-500">
                    Sé amable y evita publicar datos personales de otras personas.
                  </p>
                </div>

                {errorFormulario && (
                  <p role="alert" className="rounded-control bg-error-50 px-3 py-2 text-sm font-medium text-error-600">
                    {errorFormulario}
                  </p>
                )}

                <div>
                  <Boton type="submit" cargando={enviando}>
                    Publicar tema
                  </Boton>
                </div>
              </form>
            )}
          </Tarjeta>
        </section>
      </div>
    </Disposicion>
  )
}
