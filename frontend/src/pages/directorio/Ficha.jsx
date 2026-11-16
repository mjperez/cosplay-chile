import { useId, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import { useMeta } from '../../contexto/MetaContext'
import BotonReportar from '../../components/BotonReportar'
import Icono from '../../components/diseno/Icono'
import { Alerta, AreaTexto, Estrellas, formatoCLP, formatoFecha } from '../../components/ui'
import { REGION_CORTA } from './MapaEsquematico'

export function ubicacionDe(i, etiqueta) {
  if (i.alcance === 'INTERNACIONAL') return 'Internacional · envía a Chile'
  return [i.comuna, REGION_CORTA[i.region] || etiqueta('regiones', i.region)].filter(Boolean).join(', ')
}

export function modalidadDe(i) {
  const partes = []
  if (i.tienda_fisica) partes.push('Local físico')
  if (i.envia_a_chile && i.alcance !== 'INTERNACIONAL') partes.push('Envíos a todo Chile')
  if (i.plataforma) partes.push(i.plataforma)
  return partes.join(' · ')
}

export function especialidadDe(i, etiqueta) {
  if (i.especialidades?.length) return i.especialidades.map((e) => etiqueta('especialidades', e)).join(' · ')
  if (i.tipos_producto?.length) return i.tipos_producto.map((t) => etiqueta('tipos_producto', t)).join(' · ')
  return etiqueta('tipos_directorio', i.tipo)
}

export function Avatar({ i, tamano = 'size-[72px]', destacado = false }) {
  return i.imagen_url ? (
    <img
      src={i.imagen_url}
      alt=""
      className={`${tamano} flex-none rounded-full border-2 object-cover ${destacado ? 'border-coral' : 'border-white/60'}`}
      loading="lazy"
    />
  ) : (
    <span aria-hidden="true" className={`${tamano} inline-flex flex-none items-center justify-center rounded-full border-2 border-white/60 font-display text-2xl font-bold`}>
      {i.nombre.charAt(0)}
    </span>
  )
}

export function Precios({ i }) {
  if (i.precio_desde == null && !i.servicios?.length) return null
  return (
    <section aria-label="Precios estimados">
      <h3 className="sobretitulo mb-2 text-lavanda">Precios estimados</h3>
      {i.precio_desde != null && (
        <p className="flex justify-between border-b border-white/14 py-2 text-sm">
          <span>Rango referencial</span>
          <strong className="text-white">
            {formatoCLP(i.precio_desde)}
            {i.precio_hasta ? ` – ${formatoCLP(i.precio_hasta)}` : ''}
          </strong>
        </p>
      )}
      {i.servicios?.length > 0 && (
        <ul>
          {i.servicios.map((s) => (
            <li key={s} className="border-b border-white/14 py-2 text-sm">{s}</li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-xs text-lavanda">Referenciales. Confirma el valor directamente con el proveedor.</p>
    </section>
  )
}

export function Contacto({ i }) {
  return (
    <div className="flex flex-wrap gap-3">
      {i.contacto && (
        <p className="w-full text-sm">
          <span className="sobretitulo mr-2 text-lavanda">Contacto</span>
          <span className="break-words text-white">{i.contacto}</span>
        </p>
      )}
      {i.sitio_web && (
        <a href={i.sitio_web} target="_blank" rel="noreferrer" className="boton-marca">
          Sitio web o red social <Icono nombre="externo" tamano={14} grosor={2.2} />
          <span className="sr-only"> (se abre en otra pestaña)</span>
        </a>
      )}
    </div>
  )
}

// RF-19: calificación de 1 a 5 (botones circulares del diseño) y comentario
export function FormResena({ itemId, onListo }) {
  const id = useId()
  const [nota, setNota] = useState(0)
  const [comentario, setComentario] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)
  const enviar = async (e) => {
    e.preventDefault()
    if (!nota) return setError('Elige una calificación de 1 a 5 estrellas.')
    setEnviando(true)
    try {
      await api(`/api/directorio/${itemId}/resenas`, { method: 'POST', body: { calificacion: nota, comentario } })
      onListo()
    } catch (err) {
      setError(err.message)
    } finally {
      setEnviando(false)
    }
  }
  return (
    <form onSubmit={enviar} className="mt-4 space-y-4" aria-labelledby={`${id}-t`}>
      <h3 id={`${id}-t`} className="font-bold text-white">Deja tu reseña</h3>
      <Alerta tipo="error">{error}</Alerta>
      <fieldset>
        <legend className="rotulo">Calificación</legend>
        <div className="mt-2 flex gap-2">
          {[1, 2, 3, 4, 5].map((n) => (
            <label
              key={n}
              className={`inline-flex size-11 cursor-pointer items-center justify-center rounded-full border font-bold has-[input:focus-visible]:outline-2 has-[input:focus-visible]:outline-offset-2 has-[input:focus-visible]:outline-cian ${
                n <= nota ? 'border-estrella bg-estrella/20 text-estrella' : 'border-white/40 text-white'
              }`}
            >
              <input type="radio" name={`${id}-nota`} value={n} checked={nota === n} onChange={() => setNota(n)} className="sr-only" />
              <span aria-hidden="true">{n}</span>
              <span className="sr-only">{n} de 5 estrellas</span>
            </label>
          ))}
        </div>
      </fieldset>
      <AreaTexto
        etiqueta="Tu reseña (opcional)"
        rows={3}
        maxLength={1000}
        value={comentario}
        onChange={(e) => setComentario(e.target.value)}
        placeholder="Cuenta tu experiencia con este proveedor"
      />
      <button className="boton-contorno" disabled={enviando}>Enviar reseña</button>
    </form>
  )
}

export function Resenas({ i, recargar, limite }) {
  const { usuario } = useAuth()
  const location = useLocation()
  const lista = limite ? i.resenas.slice(0, limite) : i.resenas
  return (
    <section aria-label="Reseñas">
      <h3 className="font-display text-xl font-bold text-white">Reseñas ({i.total_resenas})</h3>
      {lista.length === 0 && <p className="mt-2 text-sm text-lavanda">Aún no hay reseñas.</p>}
      <ul className="mt-3 space-y-4">
        {lista.map((r) => (
          <li key={r.id} className="border-b border-white/12 pb-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-[13px] text-lavanda">{r.autor?.nombre} · {formatoFecha(r.created_at)}</p>
              <Estrellas valor={r.calificacion} />
            </div>
            {r.comentario && <p className="mt-1 text-sm text-white">{r.comentario}</p>}
            <BotonReportar tipo="RESENA" objetoId={r.id} compacto texto="Reportar reseña" />
          </li>
        ))}
      </ul>
      {!usuario && (
        <p className="mt-4 flex items-center gap-2 text-[13px] text-lavanda">
          <Icono nombre="candado" tamano={15} />
          <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname + location.search)}`} className="enlace-claro">
            Inicia sesión
          </Link>{' '}
          para dejar tu calificación
        </p>
      )}
      {usuario && i.puede_resenar && !i.ya_resenado && recargar && <FormResena itemId={i.id} onListo={recargar} />}
      {usuario && i.ya_resenado && <p className="mt-3 text-sm text-lavanda">Ya dejaste tu reseña. ¡Gracias!</p>}
    </section>
  )
}
