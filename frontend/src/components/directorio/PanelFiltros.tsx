import type { OpcionesDirectorio } from '../../lib/api'
import { ETIQUETAS_TIPO } from '../../lib/etiquetas'

interface Props {
  q: string
  region: string
  tipo: string
  sinRegion: boolean
  opciones: OpcionesDirectorio | null
  onCambio: (cambios: Record<string, string | null>) => void
  onLimpiar: () => void
  hayFiltros: boolean
}

export function PanelFiltros({
  q,
  region,
  tipo,
  sinRegion,
  opciones,
  onCambio,
  onLimpiar,
  hayFiltros,
}: Props) {
  return (
    <section
      aria-labelledby="titulo-filtros"
      className="rounded-tarjeta border border-tinta-200 bg-white p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="titulo-filtros" className="text-sm font-semibold text-tinta-900">
          Filtrar el directorio
        </h2>
        {hayFiltros && (
          <button
            type="button"
            onClick={onLimpiar}
            className="rounded-control px-2 py-1 text-xs font-semibold text-marca-700 hover:bg-marca-50"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <label htmlFor="filtro-q" className="text-xs font-medium text-tinta-700">
            Buscar
          </label>
          <input
            id="filtro-q"
            type="search"
            placeholder="Nombre o descripción"
            value={q}
            onChange={(evento) => onCambio({ q: evento.target.value || null })}
            className="rounded-control border border-tinta-300 bg-white px-3 py-2 text-sm placeholder:text-tinta-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="filtro-region" className="text-xs font-medium text-tinta-700">
            Región
          </label>
          <select
            id="filtro-region"
            value={region}
            onChange={(evento) => onCambio({ region: evento.target.value || null })}
            className="rounded-control border border-tinta-300 bg-white px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
          >
            <option value="">Todas las regiones</option>
            {opciones?.regiones.map((nombre) => (
              <option key={nombre} value={nombre}>
                {nombre}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="filtro-tipo" className="text-xs font-medium text-tinta-700">
            Tipo
          </label>
          <select
            id="filtro-tipo"
            value={tipo}
            onChange={(evento) => onCambio({ tipo: evento.target.value || null })}
            className="rounded-control border border-tinta-300 bg-white px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
          >
            <option value="">Todos los tipos</option>
            {opciones?.tipos.map((valor) => (
              <option key={valor} value={valor}>
                {ETIQUETAS_TIPO[valor] ?? valor}
              </option>
            ))}
          </select>
        </div>
      </div>

      {opciones?.hay_sin_region && (
        <label className="mt-4 flex items-center gap-2 text-sm text-tinta-700">
          <input
            type="checkbox"
            checked={sinRegion}
            onChange={(evento) =>
              onCambio({ sin_region: evento.target.checked ? '1' : null })
            }
            className="size-4 rounded border-tinta-300 text-marca-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
          />
          Solo fichas sin región declarada
        </label>
      )}
    </section>
  )
}
