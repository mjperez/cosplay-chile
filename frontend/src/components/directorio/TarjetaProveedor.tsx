import type { Proveedor } from '../../lib/api'
import { ETIQUETAS_TIPO, TONO_POR_TIPO } from '../../lib/etiquetas'
import { Etiqueta } from '../ui/Etiqueta'

export function TarjetaProveedor({ proveedor }: { proveedor: Proveedor }) {
  return (
    <article className="flex h-full flex-col gap-3 rounded-tarjeta border border-tinta-200 bg-white p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold leading-snug text-tinta-900">
          {proveedor.nombre}
        </h3>
        <Etiqueta tono={TONO_POR_TIPO[proveedor.tipo] ?? 'neutro'}>
          {ETIQUETAS_TIPO[proveedor.tipo] ?? proveedor.tipo}
        </Etiqueta>
      </div>

      <p className="text-xs font-medium text-tinta-600">
        {proveedor.region ?? (
          <span className="text-tinta-400">Región no declarada</span>
        )}
      </p>

      {proveedor.descripcion && (
        <p className="flex-1 text-sm leading-relaxed text-tinta-600">
          {proveedor.descripcion}
        </p>
      )}

      <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-tinta-100 pt-3 text-xs">
        {proveedor.contacto && (
          <span className="text-tinta-500">
            Contacto <span className="font-medium text-tinta-800">{proveedor.contacto}</span>
          </span>
        )}
        {proveedor.sitio_web && (
          <a
            href={proveedor.sitio_web}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-marca-700 hover:underline"
          >
            Sitio web
            <span className="sr-only"> de {proveedor.nombre} (se abre en otra pestaña)</span>
          </a>
        )}
      </div>
    </article>
  )
}
