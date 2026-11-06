import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Etiqueta } from '../components/ui/Etiqueta'
import { Tarjeta } from '../components/ui/Tarjeta'
import { api, type PaginaContenido } from '../lib/api'
import { ETIQUETAS_CONTENIDO, ETIQUETAS_NIVEL, TONO_CONTENIDO } from '../lib/contenido'

const POR_PAGINA = 9

const FILTROS = [
  { valor: '', etiqueta: 'Todo' },
  { valor: 'guia', etiqueta: 'Guías' },
  { valor: 'entrevista', etiqueta: 'Entrevistas' },
  { valor: 'articulo', etiqueta: 'Artículos' },
]

export function ContenidoPagina() {
  const [tipo, setTipo] = useState('')
  const [resultado, setResultado] = useState<PaginaContenido | null>(null)
  const [error, setError] = useState('')

  const consulta = useMemo(() => {
    const parametros = new URLSearchParams()
    if (tipo) parametros.set('tipo', tipo)
    parametros.set('limite', String(POR_PAGINA))
    return parametros.toString()
  }, [tipo])

  useEffect(() => {
    let vigente = true
    api
      .contenido(consulta)
      .then((datos) => {
        if (vigente) {
          setResultado(datos)
          setError('')
        }
      })
      .catch(() => {
        if (vigente) setError('No pudimos cargar el contenido. Revisa tu conexión.')
      })
    return () => {
      vigente = false
    }
  }, [consulta])

  return (
    <Disposicion>
      <div className="mx-auto max-w-6xl px-4 py-12">
        <header className="max-w-2xl">
          <h1 className="text-3xl font-black tracking-tight text-tinta-900">Contenidos</h1>
          <p className="mt-3 text-base text-tinta-600">
            Guías, entrevistas y artículos escritos por la comunidad. Todo lo que
            alguien aprendió haciendo, publicado para que no se pierda.
          </p>
        </header>

        <div className="mt-8 flex flex-wrap gap-2" role="group" aria-label="Filtrar por tipo">
          {FILTROS.map((filtro) => {
            const activo = tipo === filtro.valor
            return (
              <button
                key={filtro.valor || 'todo'}
                type="button"
                aria-pressed={activo}
                onClick={() => setTipo(filtro.valor)}
                className={[
                  'rounded-full px-4 py-1.5 text-sm font-medium transition-colors',
                  activo
                    ? 'bg-marca-700 text-white'
                    : 'border border-tinta-300 bg-white text-tinta-700 hover:bg-tinta-100',
                ].join(' ')}
              >
                {filtro.etiqueta}
              </button>
            )
          })}
        </div>

        {error && (
          <p role="alert" className="mt-6 rounded-control bg-error-50 px-3 py-2 text-sm text-error-600">
            {error}
          </p>
        )}

        {!error && resultado && resultado.total === 0 && (
          <div className="mt-10 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-16 text-center">
            <p className="text-base font-semibold text-tinta-900">
              Todavía no hay contenido publicado aquí
            </p>
            <p className="mx-auto mt-2 max-w-md text-sm text-tinta-600">
              Los contenidos se publican después de pasar por revisión. Si eres
              administrador, revisa la bandeja editorial.
            </p>
          </div>
        )}

        {resultado && resultado.total > 0 && (
          <ul className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {resultado.elementos.map((elemento) => (
              <Tarjeta como="li" key={elemento.id_contenido} className="flex h-full flex-col gap-3">
                <div className="flex items-start justify-between gap-2">
                  <Etiqueta tono={TONO_CONTENIDO[elemento.tipo] ?? 'neutro'}>
                    {ETIQUETAS_CONTENIDO[elemento.tipo] ?? elemento.tipo}
                  </Etiqueta>
                  <span className="text-xs font-medium text-tinta-500">
                    {ETIQUETAS_NIVEL[elemento.nivel] ?? elemento.nivel}
                  </span>
                </div>

                <h2 className="text-base font-semibold leading-snug text-tinta-900">
                  <Link
                    to={`/contenido/${elemento.id_contenido}`}
                    className="hover:text-marca-700 hover:underline"
                  >
                    {elemento.titulo}
                  </Link>
                </h2>

                {elemento.resumen && (
                  <p className="flex-1 text-sm leading-relaxed text-tinta-600">
                    {elemento.resumen}
                  </p>
                )}

                <Link
                  to={`/contenido/${elemento.id_contenido}`}
                  className="mt-auto text-sm font-semibold text-marca-700 hover:underline"
                >
                  Leer
                  <span aria-hidden="true"> →</span>
                </Link>
              </Tarjeta>
            ))}
          </ul>
        )}
      </div>
    </Disposicion>
  )
}
