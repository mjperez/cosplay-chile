import { useId } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexto/AuthContext'
import { useMeta } from '../contexto/MetaContext'
import BuscadorGlobal from '../components/BuscadorGlobal'
import Icono from '../components/diseno/Icono'
import useApi from '../components/useApi'
import { Alerta, haceTiempo, useTitulo } from '../components/ui'
import portada from '../assets/diseno/portada.jpg'
import mascaraZorro from '../assets/diseno/mascara-zorro.jpg'
import alasAureola from '../assets/diseno/alas-aureola.jpg'
import telas from '../assets/diseno/telas.jpg'
import maquillaje from '../assets/diseno/maquillaje.jpg'
import orejasGato from '../assets/diseno/orejas-gato.jpg'
import armaduraPlateada from '../assets/diseno/armadura-plateada.jpg'
import cuernos from '../assets/diseno/cuernos.jpg'
import ciberpunk from '../assets/diseno/ciberpunk.jpg'
import encapuchada from '../assets/diseno/encapuchada.jpg'

const PILARES = [
  { icono: 'libro', titulo: 'Aprende', items: ['Guías paso a paso en pesos chilenos', 'Niveles: principiante a avanzado', 'Descargables, imágenes y video'] },
  { icono: 'tienda', titulo: 'Encuentra', items: ['Cosmakers, sastrerías y fotógrafos', 'Tiendas con envío a Chile', 'Mapa interactivo por región'] },
  { icono: 'calendario', titulo: 'Conecta', items: ['Calendario nacional de eventos', 'Foros por tema y desafíos', 'Historias de cosplayers chilenos'] },
]

const SECCIONES = [
  { icono: 'libro', color: 'bg-icono-azul', titulo: 'Aprende', a: '/guias', items: ['Elección de personaje', 'Toma de medidas', 'Técnicas básicas', 'Presupuesto', 'Seguridad en eventos'] },
  { icono: 'tienda', color: 'bg-icono-morado', titulo: 'Encuentra', a: '/directorio', items: ['Cosmakers y sastrerías', 'Modeladores y pintores', 'Peluqueros y maquilladores', 'Telas, EVA y termoplásticos', 'Mapa por región'] },
  { icono: 'chat', color: 'bg-icono-coral', titulo: 'Participa', a: '/comunidad', items: ['Calendario nacional', 'Foros por tema', 'Desafíos mensuales', 'Historias de la comunidad', 'Galería con créditos'] },
]

const ROLES = [
  { img: orejasGato, titulo: 'Cosplayer', texto: 'Aprende, guarda favoritos y comparte tus trajes y tutoriales.', cta: 'Crear perfil', tipo: 'COSPLAYER' },
  { img: armaduraPlateada, titulo: 'Cosmaker, sastre o fotógrafo', texto: 'Muestra tu portafolio y recibe contactos de clientes.', cta: 'Listar mi servicio', tipo: 'COSMAKER' },
  { img: cuernos, titulo: 'Tienda', texto: 'Publica los materiales que vendes y llega a toda la comunidad.', cta: 'Registrar mi tienda', tipo: 'TIENDA' },
  { img: ciberpunk, titulo: 'Organizador', texto: 'Difunde tu convención, concurso o meetup en el calendario.', cta: 'Publicar evento', tipo: 'ORGANIZADOR' },
  { img: encapuchada, titulo: 'Visitante', texto: 'Explora guías, directorio y calendario sin necesidad de cuenta.', cta: 'Explorar ahora', a: '/guias' },
]

// Filtro rápido de la portada: un <select> con aspecto de chip que lleva a la sección filtrada
function FiltroRapido({ etiqueta, opciones, destino }) {
  const id = useId()
  const navigate = useNavigate()
  return (
    <span className="relative inline-flex">
      <label htmlFor={id} className="sr-only">{`Filtrar por ${etiqueta.toLowerCase()}`}</label>
      <select
        id={id}
        value=""
        onChange={(e) => e.target.value && navigate(destino(e.target.value))}
        className="etiqueta field-sizing-content min-h-11 max-w-[60vw] cursor-pointer appearance-none pr-9 sm:min-h-8"
      >
        <option value="">{etiqueta}</option>
        {opciones.map((o) => (
          <option key={o.valor} value={o.valor}>{o.texto}</option>
        ))}
      </select>
      <Icono nombre="abajo" tamano={14} grosor={2.2} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-tinta" />
    </span>
  )
}

function FotoCreditos({ src, alt, pie, proporcion = 'aspect-[3/4]' }) {
  return (
    <figure className="relative m-0">
      <img src={src} alt={alt || ''} className={`block w-full object-cover ${proporcion}`} loading="lazy" />
      {pie && (
        <figcaption className="absolute inset-x-0 bottom-0 bg-linear-to-b from-transparent to-[rgba(8,5,24,.88)] px-3.5 pb-3 pt-[34px] text-[12.5px] text-white">
          {pie}
        </figcaption>
      )}
    </figure>
  )
}

const creditos = (p) =>
  [p.credito_cosplayer && `Cosplay: ${p.credito_cosplayer}`, p.credito_fotografo && `Foto: ${p.credito_fotografo}`].filter(Boolean).join(' · ')

function Cifra({ icono, valor, texto }) {
  return (
    <div className="panel flex flex-[1_1_220px] items-center gap-4 px-6 py-[22px]">
      <Icono nombre={icono} tamano={34} grosor={1.5} className="text-durazno" />
      <div>
        <dd className="font-display text-[40px] leading-none font-bold text-white">{valor ?? '—'}</dd>
        <dt className="mt-1.5 text-sm text-lavanda">{texto}</dt>
      </div>
    </div>
  )
}

function FechaBloque({ iso }) {
  const d = new Date(`${iso}T12:00:00`)
  const mes = d.toLocaleDateString('es-CL', { month: 'short' }).replace('.', '')
  return (
    <span aria-hidden="true" className="w-[62px] flex-none border border-white/50 py-1.5 text-center leading-[1.1]">
      <span className="block font-display text-[26px] font-bold">{String(d.getDate()).padStart(2, '0')}</span>
      <span className="block text-[11px] uppercase tracking-[.16em] text-durazno">{mes}</span>
    </span>
  )
}

function ColumnaNovedades({ titulo, enlace, textoEnlace, claseLista = '', children }) {
  const id = useId()
  return (
    <section aria-labelledby={id} className="min-w-0">
      <div className="mb-1 flex items-center justify-between gap-3">
        <h3 id={id} className="sobretitulo">{titulo}</h3>
        <Link to={enlace} className="enlace-claro text-[13px] text-white">{textoEnlace}</Link>
      </div>
      <ul className={claseLista}>{children}</ul>
    </section>
  )
}

// RF-01: portada con acceso a todas las secciones, novedades y estadísticas
export default function Inicio() {
  useTitulo('')
  const { usuario } = useAuth()
  const { etiqueta, opciones } = useMeta()
  const [params] = useSearchParams()
  const { datos, error } = useApi('/api/inicio')
  const { datos: categorias } = useApi('/api/categorias')
  const e = datos?.estadisticas
  const trajes = datos?.trajes_recientes || []

  return (
    <div>
      {/* ---------- Portada ---------- */}
      <section
        aria-labelledby="t-portada"
        className="relative bg-noche bg-cover bg-no-repeat bg-[62%_center] lg:min-h-[840px]"
        style={{ backgroundImage: `url(${portada})` }}
      >
        <div aria-hidden="true" className="absolute inset-0 bg-[linear-gradient(180deg,rgba(10,8,32,.82)_0%,rgba(10,8,32,.92)_60%,#0a0820_100%)] lg:bg-[linear-gradient(90deg,#0a0820_0%,rgba(10,8,32,.94)_26%,rgba(10,8,32,.5)_46%,rgba(10,8,32,0)_64%)]" />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute left-[clamp(120px,22vw,320px)] top-[150px] hidden bg-[linear-gradient(165deg,#ff7a6b_0%,#c24a7e_55%,rgba(70,30,110,0)_100%)] bg-clip-text font-display text-[clamp(300px,34vw,520px)] leading-none font-extrabold text-transparent opacity-85 lg:block"
        >
          C
        </div>
        <div className="relative z-[2] flex max-w-[700px] flex-col gap-[22px] px-gutter pb-28 pt-36 lg:pb-[120px] lg:pt-[150px]">
          {params.get('cuenta') === 'eliminada' && (
            <Alerta tipo="info">Tu cuenta fue eliminada. ¡Gracias por haber sido parte de la comunidad!</Alerta>
          )}
          <h1 id="t-portada" className="m-0 font-display text-[clamp(52px,7.4vw,108px)] leading-[1.02] font-bold text-white">
            De la idea<br />al cosplay
          </h1>
          <p className="text-[clamp(12px,1.2vw,15px)] uppercase tracking-[.24em] text-rosado">La plataforma de la comunidad cosplay de Chile</p>
          <div className="mt-2.5 flex max-w-[520px] flex-col gap-2.5">
            <BuscadorGlobal variante="portada" />
            <div className="flex flex-wrap items-center gap-2">
              <span className="mr-1 text-[13px] text-lavanda">Filtrar por</span>
              <FiltroRapido etiqueta="Región" opciones={opciones('regiones')} destino={(v) => `/directorio?region=${v}`} />
              <FiltroRapido
                etiqueta="Categoría"
                opciones={(categorias || []).map((c) => ({ valor: c.slug, texto: c.nombre }))}
                destino={(v) => `/guias?categoria=${v}`}
              />
              <FiltroRapido
                etiqueta="Tipo de proveedor"
                opciones={opciones('especialidades')}
                destino={(v) => `/directorio?tipo=PROVEEDOR&especialidad=${v}`}
              />
            </div>
          </div>
          <div className="mt-1.5">
            <Link to="/guias" className="boton-contorno boton-grande">Explorar guías</Link>
          </div>
        </div>
      </section>

      {/* ---------- Aprende · Encuentra · Conecta ---------- */}
      <section
        aria-label="Qué ofrece la plataforma"
        className="relative z-[3] -mt-16 mr-[7%] flex flex-wrap gap-x-10 gap-y-7 bg-[linear-gradient(172deg,#c2456a_0%,#8d3a7c_58%,rgba(40,18,84,.35)_100%)] px-gutter pb-10 pt-[38px]"
      >
        {PILARES.map((p) => (
          <div key={p.titulo} className="flex flex-[1_1_260px] items-start gap-4">
            <Icono nombre={p.icono} tamano={40} grosor={1.4} className="text-[#ffe3dc]" />
            <div>
              <h2 className="mb-2 font-display text-2xl font-semibold text-white">{p.titulo}</h2>
              <ul className="text-sm leading-normal text-white">
                {p.items.map((i) => <li key={i} className="mb-1">{i}</li>)}
              </ul>
            </div>
          </div>
        ))}
      </section>

      {/* ---------- Presentación ---------- */}
      <section className="mx-auto box-border flex max-w-sitio flex-wrap items-center gap-x-16 gap-y-12 px-gutter py-24">
        <div className="flex min-w-0 flex-[1_1_380px] flex-col gap-[22px]">
          <h2 className="m-0 max-w-[480px] font-display text-[clamp(30px,3vw,42px)] leading-[1.12] font-bold text-white">
            Plataforma gratuita de guías, directorio y comunidad cosplay
          </h2>
          <p className="text-[15px] leading-[1.7] text-lavanda">
            Hoy la información del cosplay vive repartida entre redes sociales, grupos cerrados y videos desactualizados. Cosplay Chile la reúne en un
            solo lugar: guías pensadas para materiales y precios locales, profesionales y tiendas con ficha propia, y la agenda de eventos de todo el país.
          </p>
          <p className="text-[15px] leading-[1.7] text-lavanda">
            Está hecho primero para quien empieza: sin una curva de aprendizaje empinada, sin adivinar dónde comprar y sin enterarse tarde de la
            convención de tu región.
          </p>
          <div>
            <Link to="/guias?nivel=PRINCIPIANTE" className="boton-contorno boton-grande">Empieza aquí</Link>
          </div>
        </div>
        <div aria-hidden="true" className="flex h-[min(560px,110vw)] min-w-0 flex-[1.25_1_460px]">
          <img src={mascaraZorro} alt="" className="h-full w-[62%] object-cover" loading="lazy" />
          <img src={alasAureola} alt="" className="h-full min-w-0 flex-1 object-cover" loading="lazy" />
        </div>
      </section>

      {/* ---------- Trajes recientes (participaciones reales con créditos) ---------- */}
      {trajes.length > 0 && (
        <section aria-labelledby="t-trajes" className="mx-auto max-w-sitio px-gutter pb-20 pt-6">
          <div className="grid grid-cols-[repeat(auto-fit,minmax(min(260px,100%),1fr))] items-start gap-8">
            <div className="flex min-w-0 flex-col gap-7 md:mt-20">
              {trajes[0] && (
                <div className="w-[72%]">
                  <FotoCreditos src={trajes[0].imagen_url} alt={trajes[0].imagen_alt} pie={creditos(trajes[0])} proporcion="aspect-[4/5]" />
                </div>
              )}
              <div aria-hidden="true" className="w-[86%] bg-turquesa p-[26px]">
                <img src={maquillaje} alt="" className="block aspect-square w-full object-cover" loading="lazy" />
              </div>
            </div>
            <div className="flex min-w-0 flex-col gap-[26px]">
              <div className="flex flex-col gap-3.5">
                <h2 id="t-trajes" className="m-0 font-display text-[clamp(30px,3vw,42px)] leading-[1.12] font-bold text-white">Trajes recientes</h2>
                <p className="max-w-[360px] text-[15px] leading-[1.65] text-lavanda">
                  Los portafolios de la comunidad, con crédito al cosplayer y al fotógrafo en cada imagen.
                </p>
              </div>
              {trajes[1] && <FotoCreditos src={trajes[1].imagen_url} alt={trajes[1].imagen_alt} pie={creditos(trajes[1])} />}
            </div>
            <div className="flex min-w-0 flex-col gap-6 md:mt-10">
              <FotoCreditos src={telas} alt="" pie="Telas para el próximo proyecto" proporcion="aspect-[4/3]" />
              <div className="relative min-h-[400px]">
                <div aria-hidden="true" className="absolute -bottom-[30px] -right-[60px] size-[400px] rounded-full bg-[radial-gradient(circle_at_30%_20%,#7a2f78,#2c1456_70%)] opacity-90" />
                {trajes[2] && (
                  <div className="relative -mb-10 w-[46%]">
                    <FotoCreditos src={trajes[2].imagen_url} alt={trajes[2].imagen_alt} pie={creditos(trajes[2])} />
                  </div>
                )}
                <p className="relative ml-auto mt-6 w-[min(300px,52%)] text-sm leading-[1.65] text-white">
                  Cada traje cuenta una historia: materiales, tiempos y errores que se pueden evitar. Súbelo con créditos y compártelo con la comunidad.
                </p>
              </div>
            </div>
          </div>
          <div className="mt-10">
            <Link to="/desafios" className="boton-contorno">Ver desafíos y galería</Link>
          </div>
        </section>
      )}

      {/* ---------- Estadísticas reales ---------- */}
      <section aria-labelledby="t-cifras" className="mx-auto max-w-sitio px-gutter pb-14 pt-6">
        <h2 id="t-cifras" className="sr-only">La comunidad en cifras</h2>
        <Alerta tipo="error" className="mb-4">{error?.message}</Alerta>
        <dl className="flex flex-wrap gap-5">
          <Cifra icono="personas" valor={e?.personas} texto="Personas registradas" />
          <Cifra icono="libro" valor={e?.guias} texto="Guías publicadas" />
          <Cifra icono="tienda" valor={e && e.proveedores + e.tiendas} texto="Profesionales y tiendas" />
          <Cifra icono="calendario" valor={e?.eventos_proximos} texto="Eventos próximos" />
        </dl>
        {e && (
          <p className="mt-4 text-sm text-durazno">
            Presencia en {e.regiones_con_presencia} de las 16 regiones · {e.comunidades} comunidades · {e.temas} conversaciones en el foro
          </p>
        )}
      </section>

      {/* ---------- Qué encuentras aquí ---------- */}
      <section aria-labelledby="t-encuentras" className="relative mx-auto max-w-sitio px-gutter pb-24 pt-[72px]">
        <div aria-hidden="true" className="absolute -left-[180px] top-[200px] size-[560px] rounded-full bg-[radial-gradient(circle_at_40%_30%,rgba(122,47,120,.7),rgba(44,20,86,.1)_75%)]" />
        <div className="relative mb-16 flex flex-col items-end gap-4 text-right">
          <h2 id="t-encuentras" className="titulo-seccion m-0">Qué encuentras aquí</h2>
          <p className="max-w-[420px] text-[15px] leading-[1.65] text-lavanda">
            En el centro de la plataforma hay tres ideas: enseñar con materiales y precios locales, dar visibilidad a quienes trabajan en el rubro y
            reunir a la comunidad.
          </p>
        </div>
        <div className="relative flex flex-wrap gap-x-10 gap-y-12">
          {SECCIONES.map((s) => (
            <div key={s.titulo} className="flex flex-[1_1_260px] flex-col items-center gap-4 text-center">
              <span aria-hidden="true" className={`inline-flex size-[70px] items-center justify-center text-white ${s.color}`}>
                <Icono nombre={s.icono} tamano={35} grosor={1.6} />
              </span>
              <h3 className="font-display text-[28px] font-bold text-white">{s.titulo}</h3>
              <ul className="text-[14.5px] leading-[1.45] text-lavanda">
                {s.items.map((i) => <li key={i} className="mb-[7px]">{i}</li>)}
              </ul>
              <Link to={s.a} className="boton-contorno">
                Ver más<span className="sr-only">: {s.titulo}</span>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- Esta semana en la comunidad (datos reales) ---------- */}
      <section aria-labelledby="t-semana" className="relative mx-auto max-w-sitio px-gutter pb-24">
        <div aria-hidden="true" className="absolute left-0 top-[70px] h-[560px] w-[120px] bg-linear-to-b from-ciruela to-coral" />
        <div className="relative ml-[min(88px,8vw)] border border-white/12 bg-[rgba(22,12,52,.94)] px-[clamp(20px,4vw,56px)] pb-9 pt-11">
          <h2 id="t-semana" className="m-0 font-display text-[clamp(28px,3vw,40px)] leading-[1.12] font-bold text-white">Esta semana en la comunidad</h2>
          <p className="mb-7 mt-3.5 max-w-[640px] text-[15px] leading-[1.7] text-lavanda">
            Lo último del ecosistema cosplay chileno: eventos que se acercan, los hilos que más se están conversando y las guías recién publicadas.
          </p>
          <div className="grid gap-x-14 gap-y-10 lg:grid-cols-2">
            <ColumnaNovedades titulo="Próximos eventos" enlace="/calendario" textoEnlace="Ver calendario">
              {(datos?.proximos_eventos || []).slice(0, 4).map((ev) => (
                <li key={ev.id}>
                  <Link to={`/calendario/${ev.id}`} className="flex items-center gap-4 border-b border-white/16 py-3.5 text-white no-underline hover:text-durazno">
                    <FechaBloque iso={ev.fecha_inicio} />
                    <span className="min-w-0 flex-1">
                      <span className="block text-base font-bold">{ev.nombre}</span>
                      <span className="mt-0.5 block text-[13.5px] text-lavanda">
                        <span className="sr-only">{new Date(`${ev.fecha_inicio}T12:00:00`).toLocaleDateString('es-CL', { day: 'numeric', month: 'long' })} · </span>
                        {ev.comuna || ev.lugar} · {etiqueta('regiones', ev.region)}
                      </span>
                    </span>
                    <span className="etiqueta hidden flex-none sm:inline-flex">{etiqueta('tipos_evento', ev.tipo)}</span>
                  </Link>
                </li>
              ))}
              {datos && !datos.proximos_eventos?.length && <li className="py-3.5 text-sm text-lavanda">No hay eventos próximos publicados.</li>}
            </ColumnaNovedades>
            <ColumnaNovedades titulo="Hilos destacados" enlace="/comunidad" textoEnlace="Ir al foro">
              {(datos?.temas_destacados || []).slice(0, 4).map((t) => (
                <li key={t.id}>
                  <Link to={`/comunidad/temas/${t.id}`} className="flex items-center gap-3.5 border-b border-white/16 py-3.5 text-white no-underline hover:text-durazno">
                    <Icono nombre="chat" tamano={22} grosor={1.6} className="text-durazno" />
                    <span className="min-w-0 flex-1">
                      <span className="block text-base font-bold">{t.titulo}</span>
                      <span className="mt-0.5 block text-[13.5px] text-lavanda">{t.foro_titulo} · {haceTiempo(t.created_at)}</span>
                    </span>
                    <span className="flex-none text-[13px] text-lavanda">{t.respuestas} {t.respuestas === 1 ? 'respuesta' : 'respuestas'}</span>
                  </Link>
                </li>
              ))}
              {datos && !datos.temas_destacados?.length && <li className="py-3.5 text-sm text-lavanda">Aún no hay conversaciones.</li>}
            </ColumnaNovedades>
          </div>
          {datos?.ultimas_guias?.length > 0 && (
            <div className="mt-10">
              <ColumnaNovedades titulo="Guías nuevas" enlace="/guias" textoEnlace="Ver todas las guías" claseLista="grid gap-x-8 sm:grid-cols-2">
                  {datos.ultimas_guias.slice(0, 4).map((g) => (
                    <li key={g.id}>
                      <Link to={`/guias/${g.id}`} className="flex items-center gap-3.5 border-b border-white/16 py-3.5 text-white no-underline hover:text-durazno">
                        <Icono nombre="libro" tamano={22} grosor={1.6} className="text-durazno" />
                        <span className="min-w-0 flex-1">
                          <span className="block text-base font-bold">{g.titulo}</span>
                          <span className="mt-0.5 block text-[13.5px] text-lavanda">{g.categoria?.nombre} · {etiqueta('niveles', g.nivel)}</span>
                        </span>
                      </Link>
                    </li>
                  ))}
              </ColumnaNovedades>
            </div>
          )}
        </div>
      </section>

      {/* ---------- Hecho por y para la comunidad ---------- */}
      <section aria-labelledby="t-roles" className="mx-auto max-w-sitio px-gutter pb-24 pt-6">
        <div className="mb-12 flex flex-col items-end gap-3 text-right">
          <h2 id="t-roles" className="titulo-seccion m-0">Hecho por y para la comunidad</h2>
          <p className="max-w-[460px] text-[15px] leading-[1.65] text-lavanda">
            Cada rol tiene su perfil y sus herramientas. Crea el tuyo en minutos, o explora sin cuenta.
          </p>
        </div>
        <ul className="flex flex-wrap justify-between gap-x-7 gap-y-9">
          {ROLES.map((r) => {
            const destino = r.a || (usuario ? '/perfil' : `/registro?tipo=${r.tipo}`)
            return (
              <li key={r.titulo} className="max-w-[260px] flex-[1_1_200px]">
                <Link to={destino} className="group flex flex-col gap-3 text-white no-underline">
                  <img src={r.img} alt="" className="block aspect-[4/5] w-full object-cover" loading="lazy" />
                  <span className="font-display text-[22px] leading-[1.15] font-bold group-hover:text-durazno">{r.titulo}</span>
                  <span className="text-sm leading-normal text-lavanda">{r.texto}</span>
                  <span className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[.14em] text-durazno">
                    {usuario && r.tipo ? 'Ir a mi perfil' : r.cta} <Icono nombre="derecha" tamano={14} grosor={2.2} />
                  </span>
                </Link>
              </li>
            )
          })}
        </ul>
      </section>

      {/* ---------- Llamado final ---------- */}
      <section
        aria-labelledby="t-sumate"
        className="flex flex-col items-center gap-[22px] bg-linear-to-b from-[rgba(23,12,51,0)] to-[rgba(61,28,104,.55)] px-gutter pb-[88px] pt-[72px] text-center"
      >
        <h2 id="t-sumate" className="titulo-seccion m-0">{usuario ? 'Comparte lo que sabes' : 'Súmate a la comunidad'}</h2>
        <p className="max-w-[560px] text-base leading-[1.65] text-lavanda">
          {usuario
            ? 'Envía tu tutorial para que el equipo lo revise y lo publique, o sugiere un evento para el calendario nacional.'
            : 'Todo empieza con una cuenta gratuita: guarda tus guías, proveedores y eventos favoritos, y participa en el foro.'}
        </p>
        <div className="flex flex-wrap justify-center gap-3.5">
          {usuario ? (
            <>
              <Link to="/guias/publicar" className="boton-marca boton-grande">Enviar un tutorial</Link>
              <Link to="/calendario/sugerir" className="boton-contorno boton-grande">Sugerir un evento</Link>
            </>
          ) : (
            <>
              <Link to="/registro" className="boton-marca boton-grande">Crear cuenta gratis</Link>
              <Link to="/directorio" className="boton-contorno boton-grande">Explorar el directorio</Link>
            </>
          )}
        </div>
      </section>
    </div>
  )
}
