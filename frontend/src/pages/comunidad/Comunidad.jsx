import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import BotonReportar from '../../components/BotonReportar'
import CompartirRedes from '../../components/CompartirRedes'
import { CamposFotoCreditos, FiguraConCreditos, payloadFoto } from '../../components/FotoConCreditos'
import Icono from '../../components/diseno/Icono'
import useApi from '../../components/useApi'
import { Alerta, AreaTexto, Campo, Cargando, EncabezadoPagina, Paginacion, Selector, Vacio, haceTiempo, useTitulo } from '../../components/ui'
import NoEncontrado from '../NoEncontrado'
import { nombreMes } from '../desafios/Desafios'
import elfo from '../../assets/diseno/elfo.jpg'
import hechicera from '../../assets/diseno/hechicera.jpg'
import mucama from '../../assets/diseno/mucama.jpg'

function Iniciales({ nombre = '?' }) {
  const ini = nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase()
  return (
    <span aria-hidden="true" className="inline-flex size-12 flex-none items-center justify-center rounded-full border-2 border-white/60 bg-linear-135 from-ciruela to-uva font-bold text-white">
      {ini || '?'}
    </span>
  )
}

export function ListaTemas({ temas, mostrarForo = true }) {
  return (
    <ul className="space-y-3">
      {temas.map((t) => (
        <li key={t.id} className="border border-white/14 bg-white/5 p-[18px]">
          <div className="flex flex-wrap items-start gap-4">
            <Iniciales nombre={t.autor?.nombre} />
            <div className="min-w-0 flex-[1_1_220px]">
              <h3 className="font-display text-xl leading-tight font-bold">
                <Link to={`/comunidad/temas/${t.id}`} className="text-white no-underline hover:text-durazno">{t.titulo}</Link>
              </h3>
              <p className="mt-1 flex flex-wrap gap-x-3 text-[13px] text-lavanda">
                {mostrarForo && <Link to={`/comunidad/${t.foro_slug}`} className="font-bold text-durazno no-underline hover:text-white">{t.foro_titulo}</Link>}
                <span>{t.autor?.nombre || 'Usuario eliminado'}</span>
                <time dateTime={t.created_at}>{haceTiempo(t.created_at)}</time>
                {t.tiene_imagen && <span className="inline-flex items-center gap-1"><Icono nombre="imagen" tamano={13} /> con foto</span>}
              </p>
            </div>
            <span className="inline-flex flex-none items-center gap-1.5 text-[13px] text-lavanda">
              <Icono nombre="chat" tamano={15} /> {t.respuestas === 1 ? '1 respuesta' : `${t.respuestas} respuestas`}
            </span>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <CompartirRedes titulo={t.titulo} ruta={`/comunidad/temas/${t.id}`} />
            <BotonReportar tipo="TEMA" objetoId={t.id} variante="chip" compacto nombre={t.titulo} />
          </div>
        </li>
      ))}
    </ul>
  )
}

// RF-23 crear temas (RF-27 foto con créditos). Se usa en la página y en /comunidad/:slug/nuevo
export function FormNuevoTema({ foros, foroInicial, onCancelar, historia = false }) {
  const navigate = useNavigate()
  const [foro, setForo] = useState(foroInicial || foros?.[0]?.slug || '')
  const [titulo, setTitulo] = useState('')
  const [contenido, setContenido] = useState('')
  const [foto, setFoto] = useState({ imagen: null, credito_fotografo: '', credito_cosplayer: '' })
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  useEffect(() => {
    if (!foro && foros?.length) setForo(foroInicial || foros[0].slug)
  }, [foros, foro, foroInicial])

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      const t = await api(`/api/foros/${foro}/temas`, { method: 'POST', body: { titulo, contenido, ...payloadFoto(foto) } })
      navigate(`/comunidad/temas/${t.id}`)
    } catch (err) {
      setError(err)
    } finally {
      setEnviando(false)
    }
  }
  return (
    <form onSubmit={enviar} className="space-y-4" noValidate aria-label="Crear un tema">
      <Alerta tipo="error">{error?.message}</Alerta>
      <Campo etiqueta="Título" requerido maxLength={200} value={titulo} onChange={(e) => setTitulo(e.target.value)} error={error?.campos?.titulo}
        placeholder={historia ? 'Ej.: Cómo llegué al cosplay a los 30' : '¿Sobre qué quieres conversar?'} />
      <Selector etiqueta="Foro" requerido opciones={(foros || []).map((f) => ({ valor: f.slug, texto: f.titulo }))} value={foro} onChange={(e) => setForo(e.target.value)} />
      <AreaTexto etiqueta={historia ? 'Tu historia' : 'Mensaje'} requerido rows={6} value={contenido} onChange={(e) => setContenido(e.target.value)}
        error={error?.campos?.contenido} placeholder="Cuéntanos con detalle" />
      <CamposFotoCreditos valor={foto} onCambiar={setFoto} errores={error?.campos} />
      <div className="flex flex-wrap gap-3">
        <button className="boton-marca" disabled={enviando}>{enviando ? 'Publicando…' : 'Publicar tema'}</button>
        {onCancelar && <button type="button" className="boton-contorno" onClick={onCancelar}>Cancelar</button>}
      </div>
    </form>
  )
}

function BannerDesafio({ d }) {
  const cierre = new Date(d.anio, d.mes, 0).toLocaleDateString('es-CL', { day: 'numeric', month: 'long' })
  return (
    <section aria-labelledby="t-desafio" className="contenedor mt-10">
      <div className="flex flex-wrap items-center gap-10 bg-[linear-gradient(160deg,#c2456a_0%,#8d3a7c_60%,#3a1a6a_100%)] px-[clamp(20px,4vw,56px)] py-12">
        <div className="flex min-w-0 flex-[1_1_380px] flex-col gap-4">
          <p className="text-xs font-bold uppercase tracking-[.2em] text-rosado">Desafío del mes · {nombreMes(d.mes, d.anio)}</p>
          <h2 id="t-desafio" className="font-display text-[clamp(32px,3.6vw,48px)] leading-[1.08] font-bold text-white">{d.titulo}</h2>
          <p className="max-w-xl text-[15px] leading-relaxed text-white">{d.descripcion}</p>
          <p className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-white">
            <span className="inline-flex items-center gap-2"><Icono nombre="reloj" tamano={16} /> Hasta el {cierre}</span>
            <span className="inline-flex items-center gap-2"><Icono nombre="personas" tamano={16} /> {d.participaciones === 1 ? '1 participante' : `${d.participaciones} participantes`}</span>
          </p>
          <div className="mt-2 flex flex-wrap gap-3">
            <Link to={`/desafios/${d.id}#participar`} className="boton-claro boton-grande">Participar en el desafío</Link>
            <Link to={`/desafios/${d.id}`} className="boton-contorno boton-grande">Ver participantes</Link>
          </div>
        </div>
        <div aria-hidden="true" className="relative mx-auto hidden h-[260px] w-[340px] flex-none sm:block">
          <img src={elfo} alt="" className="absolute left-0 top-6 w-[42%] -rotate-6 border-4 border-white/10 shadow-2xl" />
          <img src={mucama} alt="" className="absolute right-0 top-8 w-[42%] rotate-6 border-4 border-white/10 shadow-2xl" />
          <img src={hechicera} alt="" className="absolute left-[29%] top-0 w-[42%] border-4 border-white/10 shadow-2xl" />
        </div>
      </div>
    </section>
  )
}

function PanelNotificaciones() {
  const { usuario } = useAuth()
  const { datos } = useApi(usuario ? '/api/notificaciones?limite=4' : null)
  const location = useLocation()
  return (
    <aside aria-labelledby="t-notif" className="panel p-5">
      <h2 id="t-notif" className="flex items-center gap-2 font-display text-xl font-bold text-white">
        <Icono nombre="campana" tamano={18} className="text-durazno" /> Notificaciones
      </h2>
      {!usuario ? (
        <p className="mt-3 text-sm text-lavanda">
          <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname)}`} className="enlace-claro">Inicia sesión</Link> para recibir avisos de
          nuevas guías, eventos y desafíos.
        </p>
      ) : (
        <ul className="mt-3">
          {(datos?.items || []).map((n) => (
            <li key={n.id} className="border-b border-white/12 py-3 last:border-b-0">
              <Link to={n.enlace || '#'} className="flex gap-2.5 text-sm text-white no-underline hover:text-durazno">
                <span aria-hidden="true" className={`mt-1.5 size-2 flex-none rounded-full ${n.leida ? 'bg-transparent' : 'bg-fucsia'}`} />
                <span>
                  {!n.leida && <span className="sr-only">Sin leer: </span>}
                  <span className={n.leida ? '' : 'font-bold'}>{n.mensaje}</span>
                  <span className="block text-xs text-lavanda">{haceTiempo(n.created_at)}</span>
                </span>
              </Link>
            </li>
          ))}
          {datos && datos.items.length === 0 && <li className="text-sm text-lavanda">No tienes notificaciones.</li>}
        </ul>
      )}
    </aside>
  )
}

// RF-22 foros por temática, RF-24 galería con créditos, RF-36 desafío del mes
export default function Comunidad() {
  const { slug } = useParams()
  const { usuario } = useAuth()
  const location = useLocation()
  const [pagina, setPagina] = useState(1)
  const [componer, setComponer] = useState(false)
  const foros = useApi('/api/foros')
  const recientes = useApi(slug ? null : '/api/temas/recientes?limite=20')
  const delForo = useApi(slug ? `/api/foros/${slug}/temas?pagina=${pagina}` : null)
  const desafios = useApi('/api/desafios')
  const inicio = useApi('/api/inicio')
  const foro = foros.datos?.find((f) => f.slug === slug)
  useTitulo(foro ? `${foro.titulo} · Comunidad` : 'Comunidad y foro')
  useEffect(() => setPagina(1), [slug])

  if (slug && delForo.error?.status === 404) return <NoEncontrado titulo="Foro no encontrado" />
  const temas = slug ? delForo.datos?.items : recientes.datos
  const cargando = slug ? delForo.cargando : recientes.cargando
  const error = slug ? delForo.error : recientes.error
  const desafio = desafios.datos?.find((d) => d.abierto)
  const galeria = inicio.datos?.trajes_recientes || []
  const nuevoHistoria = '/comunidad/historias/nuevo'

  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={slug ? [{ a: '/', texto: 'Inicio' }, { a: '/comunidad', texto: 'Comunidad' }, { texto: foro?.titulo || '…' }] : [{ a: '/', texto: 'Inicio' }, { texto: 'Comunidad' }]}
        titulo="Comunidad y foro"
        bajada="Foros por tema, historias personales, desafíos mensuales y una galería con crédito para cada cosplayer y fotógrafo. Un espacio respetuoso, moderado por el equipo."
      />

      {desafio && !slug && <BannerDesafio d={desafio} />}

      <div className="contenedor mt-12 grid grid-cols-1 items-start gap-6 lg:grid-cols-[14rem_minmax(0,1fr)] xl:grid-cols-[14rem_minmax(0,1fr)_16rem]">
        <div className="flex min-w-0 flex-col gap-6">
          <nav aria-labelledby="t-foros">
            <h2 id="t-foros" className="mb-3 font-display text-xl font-bold text-white">Foros por tema</h2>
            <ul className="flex gap-2 overflow-x-auto pb-1 lg:flex-col lg:gap-0 lg:overflow-visible">
              {[{ slug: '', titulo: 'Todos' }, ...(foros.datos || [])].map((f) => {
                const activo = (slug || '') === f.slug
                return (
                  <li key={f.slug || 'todos'} className="flex-none">
                    <Link
                      to={f.slug ? `/comunidad/${f.slug}` : '/comunidad'}
                      aria-current={activo ? 'page' : undefined}
                      className={`flex min-h-11 items-center whitespace-nowrap px-3 text-sm no-underline lg:border-b lg:border-white/12 ${
                        activo ? 'bg-linear-120 from-coral to-fucsia font-bold text-tinta-oscura' : 'text-white hover:text-durazno'
                      }`}
                    >
                      {f.titulo}
                      {f.temas !== undefined && <span className={`ml-auto pl-2 text-xs ${activo ? '' : 'text-lavanda'}`}>{f.temas}</span>}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </nav>
          <aside aria-labelledby="t-normas" className="panel hidden p-5 lg:block">
            <h2 id="t-normas" className="flex items-center gap-2 font-display text-xl font-bold text-white">
              <Icono nombre="escudo" tamano={18} className="text-durazno" /> Normas
            </h2>
            <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-lavanda">
              <li>Respeto ante todo: sin acoso ni funas.</li>
              <li>Da crédito a quien hizo el traje y a quien tomó la foto.</li>
              <li>Reporta lo que incumpla las normas.</li>
            </ul>
          </aside>
        </div>

        <section aria-labelledby="t-temas" className="min-w-0">
          <h2 id="t-temas" className="sr-only">{foro ? `Temas de ${foro.titulo}` : 'Temas recientes'}</h2>
          {foro && <p className="mb-4 text-sm text-lavanda">{foro.categoria}</p>}
          <div className="panel mb-4 p-4">
            {!usuario ? (
              <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname)}`} className="flex min-h-11 items-center gap-3 text-[15px] text-lavanda no-underline hover:text-white">
                <Icono nombre="mas" tamano={18} /> Crear un tema nuevo… (requiere sesión)
              </Link>
            ) : componer ? (
              <div>
                <h3 className="mb-4 font-display text-xl font-bold text-white">Nuevo tema</h3>
                <FormNuevoTema foros={foros.datos} foroInicial={slug} onCancelar={() => setComponer(false)} />
              </div>
            ) : (
              <button type="button" onClick={() => setComponer(true)} aria-expanded={componer} className="flex min-h-11 w-full items-center gap-3 text-left text-[15px] text-lavanda hover:text-white">
                <Icono nombre="mas" tamano={18} /> Crear un tema nuevo…
              </button>
            )}
          </div>
          {cargando && <Cargando />}
          <Alerta tipo="error">{error?.message}</Alerta>
          {temas && (temas.length === 0 ? <Vacio>Aún no hay temas en este foro. ¡Abre el primero!</Vacio> : <ListaTemas temas={temas} mostrarForo={!slug} />)}
          {slug && delForo.datos && <Paginacion pagina={delForo.datos.pagina} paginas={delForo.datos.paginas} onCambiar={setPagina} />}
        </section>

        <div className="lg:col-span-2 xl:col-span-1">
          <PanelNotificaciones />
        </div>
      </div>

      {galeria.length > 0 && (
        <section aria-labelledby="t-galeria" className="contenedor mt-24">
          <div className="mb-10 flex flex-wrap items-end justify-between gap-6">
            <h2 id="t-galeria" className="titulo-seccion">Galería de la comunidad</h2>
            <p className="max-w-md text-[15px] text-lavanda">Toda foto se publica con crédito al cosplayer y al fotógrafo. Puedes compartirla en tus redes con un toque.</p>
          </div>
          <ul className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {galeria.map((p) => (
              <li key={p.id} className="relative">
                <FiguraConCreditos url={p.imagen_url} alt={p.imagen_alt} cosplayer={p.credito_cosplayer} fotografo={p.credito_fotografo} proporcion="aspect-[3/4]" />
                <span className="absolute right-2 top-2">
                  <CompartirRedes titulo={p.titulo} ruta="/desafios" />
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-6">
            <Link to="/desafios" className="boton-contorno">Ver todos los desafíos</Link>
          </p>
        </section>
      )}

      <section aria-labelledby="t-historia" className="contenedor mt-24">
        <div className="flex flex-wrap items-center justify-between gap-6 border border-white/12 bg-[rgba(22,12,52,.94)] px-[clamp(20px,4vw,56px)] py-12">
          <div className="max-w-2xl">
            <h2 id="t-historia" className="font-display text-[clamp(28px,3vw,40px)] leading-tight font-bold text-white">Cuéntanos cómo empezaste</h2>
            <p className="mt-3 text-[15px] leading-relaxed text-lavanda">
              Comparte cómo entraste al mundo del cosplay para que quienes empiezan se sientan acompañados. Tu historia puede ser el primer paso de
              otra persona.
            </p>
          </div>
          <Link to={usuario ? nuevoHistoria : `/ingresar?siguiente=${encodeURIComponent(nuevoHistoria)}`} className="boton-marca boton-grande">
            Publicar mi historia
          </Link>
        </div>
      </section>
    </div>
  )
}
