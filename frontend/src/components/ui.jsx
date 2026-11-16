import { useEffect, useId } from 'react'
import { Link } from 'react-router-dom'
import Icono from './diseno/Icono'

export function useTitulo(titulo) {
  useEffect(() => {
    document.title = titulo ? `${titulo} · Cosplay Chile` : 'Cosplay Chile'
  }, [titulo])
}

function Ayuda({ id, error, ayuda }) {
  return (
    <>
      {ayuda && <p id={`${id}-ayuda`} className="ayuda">{ayuda}</p>}
      {error && <p id={`${id}-error`} className="mensaje-error">{error}</p>}
    </>
  )
}

function describedBy(id, error, ayuda) {
  return [ayuda && `${id}-ayuda`, error && `${id}-error`].filter(Boolean).join(' ') || undefined
}

function Rotulo({ id, etiqueta, requerido }) {
  return (
    <label htmlFor={id} className="rotulo">
      {etiqueta}
      {requerido && <span className="text-[var(--error)]" aria-hidden="true"> *</span>}
    </label>
  )
}

export function Campo({ etiqueta, error, ayuda, requerido, className = '', ...props }) {
  const id = useId()
  return (
    <div className={className}>
      <Rotulo id={id} etiqueta={etiqueta} requerido={requerido} />
      <input
        id={id}
        className="campo"
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy(id, error, ayuda)}
        required={requerido}
        {...props}
      />
      <Ayuda id={id} error={error} ayuda={ayuda} />
    </div>
  )
}

export function AreaTexto({ etiqueta, error, ayuda, requerido, className = '', rows = 4, ...props }) {
  const id = useId()
  return (
    <div className={className}>
      <Rotulo id={id} etiqueta={etiqueta} requerido={requerido} />
      <textarea
        id={id}
        rows={rows}
        className="campo"
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy(id, error, ayuda)}
        required={requerido}
        {...props}
      />
      <Ayuda id={id} error={error} ayuda={ayuda} />
    </div>
  )
}

export function Selector({ etiqueta, error, ayuda, requerido, opciones, vacio, className = '', ...props }) {
  const id = useId()
  return (
    <div className={className}>
      <Rotulo id={id} etiqueta={etiqueta} requerido={requerido} />
      <select
        id={id}
        className="campo"
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy(id, error, ayuda)}
        required={requerido}
        {...props}
      >
        {vacio !== undefined && <option value="">{vacio}</option>}
        {opciones.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.texto}
          </option>
        ))}
      </select>
      <Ayuda id={id} error={error} ayuda={ayuda} />
    </div>
  )
}

export function Casilla({ etiqueta, error, ayuda, className = '', ...props }) {
  const id = useId()
  return (
    <div className={className}>
      <div className="flex items-start gap-3">
        <input
          id={id}
          type="checkbox"
          className="mt-0.5 h-5 w-5 shrink-0 accent-coral"
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={describedBy(id, error, ayuda)}
          {...props}
        />
        <label htmlFor={id} className="text-sm leading-relaxed">{etiqueta}</label>
      </div>
      <Ayuda id={id} error={error} ayuda={ayuda} />
    </div>
  )
}

export function Alerta({ tipo = 'info', children, className = '' }) {
  if (!children) return null
  const rol = tipo === 'error' ? 'alert' : 'status'
  return (
    <div role={rol} className={`alerta-${tipo} ${className}`}>
      {children}
    </div>
  )
}

export function Cargando({ texto = 'Cargando…' }) {
  return (
    <p role="status" className="texto-suave flex items-center gap-2 py-8">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-coral border-t-transparent" aria-hidden="true" />
      {texto}
    </p>
  )
}

export function Vacio({ children }) {
  return <p className="panel texto-suave border-dashed p-8 text-center">{children}</p>
}

export function Paginacion({ pagina, paginas, onCambiar }) {
  if (!paginas || paginas <= 1) return null
  return (
    <nav aria-label="Paginación" className="mt-8 flex flex-wrap items-center justify-center gap-3">
      <button className="boton-contorno" disabled={pagina <= 1} onClick={() => onCambiar(pagina - 1)}>
        <Icono nombre="izquierda" tamano={14} grosor={2.2} /> Anterior
      </button>
      <span aria-current="page" className="texto-suave text-sm">
        Página {pagina} de {paginas}
      </span>
      <button className="boton-contorno" disabled={pagina >= paginas} onClick={() => onCambiar(pagina + 1)}>
        Siguiente <Icono nombre="derecha" tamano={14} grosor={2.2} />
      </button>
    </nav>
  )
}

// Encabezado de página del diseño: migas, título grande en Playfair y bajada a la derecha
export function EncabezadoPagina({ migas, titulo, bajada, children, id = 'titulo-pagina' }) {
  return (
    <div className="contenedor pt-8 sm:pt-12">
      {migas && <Migas items={migas} />}
      <div className="flex flex-wrap items-end justify-between gap-x-16 gap-y-6">
        <h1 id={id} className="max-w-3xl font-display text-[clamp(44px,6vw,84px)] leading-[1.02] font-bold text-white">
          {titulo}
        </h1>
        {bajada && <p className="texto-suave max-w-md text-[15px] leading-relaxed">{bajada}</p>}
      </div>
      {children}
    </div>
  )
}

export function Migas({ items }) {
  return (
    <nav aria-label="Ruta" className="mb-6 text-[13px]">
      <ol className="texto-suave flex flex-wrap items-center gap-1">
        {items.map((it, i) => (
          <li key={i} className="flex items-center gap-1">
            {i > 0 && <span aria-hidden="true">/</span>}
            {it.a ? (
              <Link to={it.a} className="enlace-claro">
                {it.texto}
              </Link>
            ) : (
              <span aria-current="page">{it.texto}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

// Grupo de filtros con chips (botones conmutables, aria-pressed)
export function GrupoChips({ etiqueta, opciones, valor, onCambiar, className = '' }) {
  const id = useId()
  return (
    <div role="group" aria-labelledby={id} className={`flex flex-wrap items-center gap-2 ${className}`}>
      <span id={id} className="sobretitulo mr-3 min-w-20">{etiqueta}</span>
      {opciones.map((o) => (
        <button
          key={o.valor || 'todos'}
          type="button"
          className="chip-filtro"
          aria-pressed={valor === o.valor}
          onClick={() => onCambiar(o.valor)}
        >
          {o.texto}
        </button>
      ))}
    </div>
  )
}

export function Estrellas({ valor, total }) {
  const v = Math.round((valor || 0) * 10) / 10
  return (
    <span
      className="inline-flex items-center gap-1.5"
      aria-label={v ? `${v.toLocaleString('es-CL')} de 5 estrellas${total !== undefined ? `, ${total} reseñas` : ''}` : 'Sin reseñas'}
    >
      <Icono nombre="estrella" tamano={15} className="text-[var(--estrella)]" relleno={v ? 'currentColor' : 'none'} />
      <span aria-hidden="true" className="text-[13px]">
        {v ? <span className="text-[var(--estrella)]">{v.toLocaleString('es-CL', { minimumFractionDigits: 1 })}</span> : <span className="texto-suave">Sin reseñas</span>}
        {total ? <span className="texto-suave"> ({total} {total === 1 ? 'reseña' : 'reseñas'})</span> : ''}
      </span>
    </span>
  )
}

export function formatoFecha(iso, opciones = { day: 'numeric', month: 'long', year: 'numeric' }) {
  if (!iso) return ''
  const d = iso.length === 10 ? new Date(`${iso}T12:00:00`) : new Date(iso)
  return d.toLocaleDateString('es-CL', opciones)
}

// «hace 2 h», «ayer», «hace 3 días»
export function haceTiempo(iso, ahora = Date.now()) {
  if (!iso) return ''
  const seg = Math.round((new Date(iso).getTime() - ahora) / 1000)
  const rtf = new Intl.RelativeTimeFormat('es-CL', { numeric: 'auto', style: 'short' })
  const abs = Math.abs(seg)
  if (abs < 60) return 'recién'
  if (abs < 3600) return rtf.format(Math.round(seg / 60), 'minute')
  if (abs < 86400) return rtf.format(Math.round(seg / 3600), 'hour')
  if (abs < 86400 * 30) return rtf.format(Math.round(seg / 86400), 'day')
  return formatoFecha(iso)
}

export function formatoCLP(n) {
  if (n === null || n === undefined) return ''
  return n.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 })
}
