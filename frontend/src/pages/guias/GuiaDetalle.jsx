import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { descargar } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import { useMeta } from '../../contexto/MetaContext'
import BotonFavorito from '../../components/BotonFavorito'
import BotonReportar from '../../components/BotonReportar'
import CompartirRedes from '../../components/CompartirRedes'
import TextoRico from '../../components/TextoRico'
import Icono from '../../components/diseno/Icono'
import { InsigniaNivel } from '../../components/diseno/Insignias'
import useApi from '../../components/useApi'
import { Alerta, Cargando, Migas, formatoFecha, useTitulo } from '../../components/ui'
import NoEncontrado from '../NoEncontrado'

function Seccion({ id, titulo, children }) {
  return (
    <section className="mt-12" aria-labelledby={id}>
      <h2 id={id} className="mb-4 font-display text-[clamp(26px,2.6vw,34px)] font-bold text-white">{titulo}</h2>
      {children}
    </section>
  )
}

export default function GuiaDetalle() {
  const { id } = useParams()
  const { usuario } = useAuth()
  const { etiqueta } = useMeta()
  const location = useLocation()
  const { datos: c, error, cargando } = useApi(`/api/contenidos/${id}`)
  const [errorDescarga, setErrorDescarga] = useState('')
  useTitulo(c?.titulo || 'Guía')

  if (cargando) return <div className="contenedor"><Cargando /></div>
  if (error?.status === 404 || error?.status === 422) return <NoEncontrado titulo="Guía no encontrada" />
  if (error) return <div className="contenedor py-10"><Alerta tipo="error">{error.message}</Alerta></div>
  if (!c) return null

  const bajar = async () => {
    setErrorDescarga('')
    try {
      await descargar(`/api/contenidos/${c.id}/descargar`, 'guia.html')
    } catch (e) {
      setErrorDescarga(e.message)
    }
  }

  return (
    <article className="pb-24">
      {/* ---------- Cabecera ---------- */}
      <header className="contenedor flex flex-wrap items-center gap-x-16 gap-y-10 pt-8 sm:pt-12">
        <div className="flex min-w-0 flex-[1.2_1_420px] flex-col gap-4">
          <Migas items={[{ texto: 'Inicio', a: '/' }, { texto: 'Guías', a: '/guias' }, { texto: c.categoria.nombre, a: `/guias?categoria=${c.categoria.slug}` }, { texto: c.titulo }]} />
          {c.estado !== 'PUBLICADO' && (
            <Alerta tipo={c.estado === 'RECHAZADO' ? 'error' : 'aviso'}>
              Estado: <strong>{etiqueta('estados_publicacion', c.estado)}</strong>. Solo tú y el equipo de moderación pueden verlo.
              {c.motivo_rechazo && <> Motivo: {c.motivo_rechazo}</>}
            </Alerta>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <InsigniaNivel nivel={c.nivel} />
            <span className="etiqueta">{etiqueta('tipos_contenido', c.tipo)}</span>
            <span className="sobretitulo ml-2">{c.categoria.nombre}</span>
          </div>
          <h1 className="font-display text-[clamp(38px,5vw,68px)] leading-[1.05] font-bold text-white">{c.titulo}</h1>
          <p className="max-w-2xl text-lg leading-relaxed text-lavanda">{c.descripcion}</p>
          <p className="text-sm text-lavanda">
            Por <span className="text-white">{c.autor?.nombre || 'Cosplay Chile'}</span> · {formatoFecha(c.publicado_at || c.created_at)}
          </p>
          {c.estado === 'PUBLICADO' && (
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <BotonFavorito tipo="CONTENIDO" objetoId={c.id} inicial={c.es_favorito} />
              {usuario ? (
                <button className="boton-contorno" onClick={bajar}>
                  <Icono nombre="descargar" tamano={16} /> Descargar
                </button>
              ) : (
                <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname)}`} className="boton-contorno">
                  <Icono nombre="descargar" tamano={16} /> Inicia sesión para descargar
                </Link>
              )}
              <CompartirRedes titulo={c.titulo} ruta={`/guias/${c.id}`} variante="boton" />
              <BotonReportar tipo="CONTENIDO" objetoId={c.id} />
            </div>
          )}
          <Alerta tipo="error">{errorDescarga}</Alerta>
        </div>
        {c.imagen_url && (
          <div className="relative mx-auto w-full max-w-[460px] flex-[1_1_320px]">
            <div aria-hidden="true" className="absolute -right-6 -top-6 h-full w-full bg-linear-to-b from-coral to-uva" />
            <img src={c.imagen_url} alt={c.imagen_alt || ''} className="relative block aspect-[4/3] w-full object-cover" />
          </div>
        )}
      </header>

      <div className="contenedor">
        <div className="max-w-3xl">
          {c.cuerpo && <TextoRico texto={c.cuerpo} className="mt-12 text-lg leading-relaxed text-tinta" />}

          {c.materiales?.length > 0 && (
            <Seccion id="t-materiales" titulo="Materiales">
              <ul className="panel grid gap-2 p-6 sm:grid-cols-2">
                {c.materiales.map((m, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-[15px]">
                    <Icono nombre="check" tamano={18} grosor={2.2} className="mt-0.5 text-exito" /> {m}
                  </li>
                ))}
              </ul>
            </Seccion>
          )}
          {c.pasos?.length > 0 && (
            <Seccion id="t-pasos" titulo="Paso a paso">
              <ol className="space-y-3">
                {c.pasos.map((p, i) => (
                  <li key={i} className="panel flex gap-4 p-4">
                    <span aria-hidden="true" className="font-display text-3xl leading-none font-bold text-durazno">{String(i + 1).padStart(2, '0')}</span>
                    <span className="pt-1 text-[15px] leading-relaxed"><span className="sr-only">Paso {i + 1}: </span>{p}</span>
                  </li>
                ))}
              </ol>
            </Seccion>
          )}
          {c.preguntas?.length > 0 && (
            <Seccion id="t-entrevista" titulo={`Entrevista a ${c.entrevistado}`}>
              <dl className="space-y-6">
                {c.preguntas.map((p, i) => (
                  <div key={i} className="border-l-2 border-coral pl-5">
                    <dt className="font-bold text-durazno">{p}</dt>
                    <dd className="mt-2 leading-relaxed text-tinta">{c.respuestas?.[i]}</dd>
                  </div>
                ))}
              </dl>
            </Seccion>
          )}
          {c.video_embed && (
            <Seccion id="t-video" titulo="Video">
              <div className="aspect-video overflow-hidden border border-white/16 bg-noche">
                <iframe src={c.video_embed} title={`Video: ${c.titulo}`} className="h-full w-full" loading="lazy"
                  allow="accelerometer; encrypted-media; gyroscope; picture-in-picture" allowFullScreen />
              </div>
              <p className="mt-2 text-sm">
                <a href={c.video_url} className="enlace-claro" target="_blank" rel="noreferrer">Ver el video en su sitio original</a>
              </p>
            </Seccion>
          )}
          {c.enlaces?.length > 0 && (
            <Seccion id="t-referencias" titulo="Referencias">
              <ul className="space-y-2">
                {c.enlaces.map((u) => (
                  <li key={u}><a href={u} className="enlace-claro break-all" target="_blank" rel="noreferrer">{u}</a></li>
                ))}
              </ul>
            </Seccion>
          )}
          <div className="mt-14 border-t border-white/12 pt-8">
            <Link to={`/guias?categoria=${c.categoria.slug}`} className="boton-contorno">
              <Icono nombre="izquierda" tamano={14} grosor={2.2} /> Más guías de {c.categoria.nombre}
            </Link>
          </div>
        </div>
      </div>
    </article>
  )
}
