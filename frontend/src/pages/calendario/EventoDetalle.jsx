import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import { useMeta } from '../../contexto/MetaContext'
import BotonFavorito from '../../components/BotonFavorito'
import BotonReportar from '../../components/BotonReportar'
import CompartirRedes from '../../components/CompartirRedes'
import Icono from '../../components/diseno/Icono'
import { InsigniaEvento } from '../../components/diseno/Insignias'
import useApi from '../../components/useApi'
import { Alerta, Cargando, Migas, formatoFecha, useTitulo } from '../../components/ui'
import NoEncontrado from '../NoEncontrado'

// RF-16: nombre, fecha, lugar, tipo y enlace oficial; RF-17 reportar actualizaciones
export default function EventoDetalle() {
  const { id } = useParams()
  const { usuario } = useAuth()
  const { etiqueta } = useMeta()
  const location = useLocation()
  const { datos: e, error, cargando } = useApi(`/api/eventos/${id}`)
  const [asistencia, setAsistencia] = useState(null)
  const [errorAsistencia, setErrorAsistencia] = useState('')
  useTitulo(e?.nombre || 'Evento')

  if (cargando) return <div className="contenedor"><Cargando /></div>
  if (error?.status === 404 || error?.status === 422) return <NoEncontrado titulo="Evento no encontrado" />
  if (error) return <div className="contenedor py-10"><Alerta tipo="error">{error.message}</Alerta></div>
  if (!e) return null

  const estado = asistencia || { asistire: e.asistire, asistentes: e.asistentes }
  const alternarAsistencia = async () => {
    setErrorAsistencia('')
    try {
      setAsistencia(await api(`/api/eventos/${e.id}/asistir`, { method: 'POST' }))
    } catch (err) {
      setErrorAsistencia(err.message)
    }
  }
  const inicio = new Date(`${e.fecha_inicio}T12:00:00`)

  return (
    <article className="contenedor pb-24 pt-8 sm:pt-12">
      <Migas items={[{ texto: 'Inicio', a: '/' }, { texto: 'Calendario', a: '/calendario' }, { texto: e.nombre }]} />
      {e.estado !== 'PUBLICADO' && (
        <Alerta tipo="aviso" className="mb-6">
          Esta sugerencia está {etiqueta('estados_publicacion', e.estado).toLowerCase()}. Solo tú y moderación pueden verla.
        </Alerta>
      )}
      <div className="grid items-start gap-10 lg:grid-cols-[1fr_24rem]">
        <div className="min-w-0">
          <div className="flex items-start gap-5">
            <span aria-hidden="true" className="w-[78px] flex-none border border-white/50 py-2 text-center leading-[1.1]">
              <span className="block font-display text-4xl font-bold text-white">{inicio.getDate()}</span>
              <span className="block text-xs uppercase tracking-[.16em] text-durazno">{inicio.toLocaleDateString('es-CL', { month: 'short' }).replace('.', '')}</span>
            </span>
            <div className="min-w-0">
              <InsigniaEvento tipo={e.tipo} />
              <h1 className="mt-3 font-display text-[clamp(36px,5vw,64px)] leading-[1.05] font-bold text-white">{e.nombre}</h1>
            </div>
          </div>
          {e.imagen_url && <img src={e.imagen_url} alt={e.imagen_alt || ''} className="mt-8 w-full max-w-3xl object-cover" />}
          {e.descripcion && <p className="mt-8 max-w-3xl whitespace-pre-line text-lg leading-relaxed text-tinta">{e.descripcion}</p>}
          <p className="mt-8">
            <Link to="/seguridad#consejos" className="enlace-claro">Consejos de seguridad para asistir a eventos</Link>
          </p>
        </div>

        <aside aria-label="Datos del evento" className="panel flex flex-col gap-5 p-6 lg:sticky lg:top-4">
          <dl className="space-y-4">
            <div>
              <dt className="sobretitulo text-lavanda">Fecha</dt>
              <dd className="mt-1 text-white">
                {formatoFecha(e.fecha_inicio, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
                {e.fecha_fin && e.fecha_fin !== e.fecha_inicio && <> al {formatoFecha(e.fecha_fin, { weekday: 'long', day: 'numeric', month: 'long' })}</>}
              </dd>
            </div>
            <div>
              <dt className="sobretitulo text-lavanda">Lugar</dt>
              <dd className="mt-1 text-white">{e.lugar}{e.comuna ? `, ${e.comuna}` : ''}</dd>
              <dd className="text-sm text-lavanda">Región {etiqueta('regiones', e.region)}</dd>
            </div>
          </dl>
          {e.enlace_oficial && (
            <a href={e.enlace_oficial} target="_blank" rel="noreferrer" className="boton-marca">
              Sitio oficial y entradas <Icono nombre="externo" tamano={14} grosor={2.2} />
              <span className="sr-only"> (sitio externo, se abre en otra pestaña)</span>
            </a>
          )}
          {e.estado === 'PUBLICADO' && (
            <div className="flex flex-wrap items-center gap-3">
              {usuario ? (
                <button className={estado.asistire ? 'boton-marca' : 'boton-contorno'} aria-pressed={estado.asistire} onClick={alternarAsistencia}>
                  <Icono nombre="check" tamano={16} grosor={2.2} /> Asistiré
                </button>
              ) : (
                <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname)}`} className="boton-contorno">Inicia sesión para marcar «Asistiré»</Link>
              )}
              <BotonFavorito variante="icono" tipo="EVENTO" objetoId={e.id} inicial={e.es_favorito} nombre={e.nombre} />
              <CompartirRedes titulo={e.nombre} ruta={`/calendario/${e.id}`} />
            </div>
          )}
          <Alerta tipo="error">{errorAsistencia}</Alerta>
          <p className="text-sm text-lavanda" aria-live="polite">
            {estado.asistentes === 1 ? '1 persona de la comunidad asistirá' : `${estado.asistentes} personas de la comunidad asistirán`}
          </p>
          {e.estado === 'PUBLICADO' && <BotonReportar tipo="EVENTO" objetoId={e.id} />}
          <p className="text-xs text-lavanda">Cosplay Chile no vende entradas: el enlace te lleva al sitio oficial del evento.</p>
        </aside>
      </div>
    </article>
  )
}
