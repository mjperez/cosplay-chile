import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import BotonReportar from '../../components/BotonReportar'
import CompartirRedes from '../../components/CompartirRedes'
import { FiguraConCreditos } from '../../components/FotoConCreditos'
import useApi from '../../components/useApi'
import { Alerta, AreaTexto, Cargando, Migas, useTitulo } from '../../components/ui'
import NoEncontrado from '../NoEncontrado'

const fecha = (f) => new Date(f).toLocaleString('es-CL', { dateStyle: 'medium', timeStyle: 'short' })

export default function TemaDetalle() {
  const { id } = useParams()
  const { usuario } = useAuth()
  const location = useLocation()
  const { datos: t, error, cargando, recargar } = useApi(`/api/temas/${id}`)
  const [respuesta, setRespuesta] = useState('')
  const [errorResp, setErrorResp] = useState(null)
  const [aviso, setAviso] = useState('')
  useTitulo(t?.titulo || 'Tema')

  if (cargando && !t) return <div className="contenedor"><Cargando /></div>
  if (error?.status === 404 || error?.status === 422) return <NoEncontrado titulo="Tema no encontrado" />
  if (error) return <div className="contenedor py-10"><Alerta tipo="error">{error.message}</Alerta></div>
  if (!t) return null

  const responder = async (e) => {
    e.preventDefault()
    setErrorResp(null)
    try {
      await api(`/api/temas/${t.id}/respuestas`, { method: 'POST', body: { contenido: respuesta } })
      setRespuesta('')
      setAviso('Tu respuesta fue publicada.')
      recargar()
    } catch (err) {
      setErrorResp(err)
    }
  }

  return (
    <div className="contenedor max-w-4xl pb-24 pt-8 sm:pt-12">
      <Migas items={[{ texto: 'Inicio', a: '/' }, { texto: 'Comunidad', a: '/comunidad' }, { texto: t.foro.titulo, a: `/comunidad/${t.foro.slug}` }, { texto: t.titulo }]} />
      {t.oculto && <Alerta tipo="aviso" className="mb-4">Este tema fue ocultado por moderación (solo lo ves por tu rol).</Alerta>}
      <article className="panel p-6 sm:p-8">
        <p className="sobretitulo">{t.foro.titulo}</p>
        <h1 className="mt-2 font-display text-[clamp(32px,4vw,52px)] leading-[1.08] font-bold text-white">{t.titulo}</h1>
        <p className="mt-2 text-sm text-lavanda">
          {t.autor?.nombre || 'Usuario eliminado'} · <time dateTime={t.created_at}>{fecha(t.created_at)}</time>
        </p>
        <p className="mt-6 whitespace-pre-line text-lg leading-relaxed text-tinta">{t.contenido}</p>
        <FiguraConCreditos url={t.imagen_url} alt={t.imagen_alt} fotografo={t.credito_fotografo} cosplayer={t.credito_cosplayer} className="mt-6 max-w-xl" />
        <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-white/12 pt-4">
          <CompartirRedes titulo={t.titulo} ruta={`/comunidad/temas/${t.id}`} variante="boton" />
          <BotonReportar tipo="TEMA" objetoId={t.id} />
        </div>
      </article>

      <section className="mt-10" aria-labelledby="t-respuestas">
        <h2 id="t-respuestas" className="mb-4 font-display text-3xl font-bold text-white">
          {t.respuestas.length === 1 ? '1 respuesta' : `${t.respuestas.length} respuestas`}
        </h2>
        <ol className="space-y-3">
          {t.respuestas.map((r) => (
            <li key={r.id} id={`respuesta-${r.id}`} className="scroll-mt-24 border border-white/14 bg-white/5 p-5">
              <p className="text-sm font-bold text-white">
                {r.autor?.nombre || 'Usuario eliminado'} <span className="font-normal text-lavanda">· {fecha(r.created_at)}</span>
              </p>
              <p className="mt-2 whitespace-pre-line text-tinta">{r.contenido}</p>
              <BotonReportar tipo="RESPUESTA" objetoId={r.id} compacto texto="Reportar respuesta" />
            </li>
          ))}
        </ol>
        <Alerta tipo="exito" className="mt-4">{aviso}</Alerta>
        {usuario ? (
          <form onSubmit={responder} className="panel mt-6 space-y-4 p-6">
            <Alerta tipo="error">{errorResp?.message}</Alerta>
            <AreaTexto etiqueta="Tu respuesta" rows={4} requerido value={respuesta} onChange={(e) => setRespuesta(e.target.value)} error={errorResp?.campos?.contenido} />
            <button className="boton-marca">Responder</button>
          </form>
        ) : (
          <p className="mt-6 text-lavanda">
            <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname)}`} className="enlace-claro">Inicia sesión</Link> para responder.
          </p>
        )}
      </section>
    </div>
  )
}
