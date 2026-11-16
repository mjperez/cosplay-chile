import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { qs } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import { useMeta } from '../../contexto/MetaContext'
import Acordeon from '../../components/diseno/Acordeon'
import Icono from '../../components/diseno/Icono'
import useApi from '../../components/useApi'
import useFavoritos from '../../components/useFavoritos'
import { Alerta, Cargando, GrupoChips, Migas, Paginacion, Vacio, useTitulo } from '../../components/ui'
import TarjetaContenido from './TarjetaContenido'
import maniqui from '../../assets/diseno/maniqui.jpg'
import armaduraPlateada from '../../assets/diseno/armadura-plateada.jpg'

const ERRORES = [
  ['Comprar la tela sin probar su caída', 'Pide una muestra y mira cómo cae antes de cortar: cambia por completo el resultado final.'],
  ['No sellar la espuma EVA antes de pintar', 'Sin sellador, la pintura se absorbe y se agrieta con el movimiento del traje.'],
  ['Usar la peluca sin fijar ni peinar', 'Una peluca sin estilizar delata el traje. Córtala, fíjala y pruébala antes del evento.'],
  ['Estrenar el traje el mismo día', 'Pruébalo sentado, caminando y subiendo escaleras para descubrir dónde aprieta o se rompe.'],
]

const SEGURIDAD = [
  { icono: 'alerta', titulo: 'Acoso', texto: 'Cómo reconocerlo, qué hacer y a quién pedir ayuda dentro del recinto.' },
  { icono: 'transporte', titulo: 'Transporte', texto: 'Llegar y volver con seguridad cuando vas disfrazado o con piezas voluminosas.' },
  { icono: 'salud', titulo: 'Salud', texto: 'Hidratación, descansos y cuidado de la piel con maquillaje, lentes y pelucas.' },
]

// RF-30 (parcial): preguntas frecuentes estáticas; no son autoadministrables (ver docs/BRECHAS_DISENO.md)
const FAQ = [
  ['¿Necesito saber coser para empezar?', 'No. Hay guías para trajes sin costura: espuma EVA, adhesivos y prendas base que puedes adaptar. Cuando quieras aprender, las guías de confección parten desde cero.'],
  ['¿Cuánto cuesta hacer un cosplay?', 'Depende del personaje y de los materiales. Las guías de presupuesto usan precios en pesos chilenos y proponen alternativas más baratas o reutilizables.'],
  ['¿Puedo descargar las guías?', 'Sí. Con una cuenta, cada guía tiene un botón de descarga en un formato que puedes imprimir o guardar como PDF. También puedes guardarlas en favoritos.'],
  ['¿Cómo publico mi propio tutorial?', 'Con una cuenta, usa el formulario «Enviar mi tutorial». Tu tutorial queda pendiente de revisión y te avisamos con una notificación cuando se publique.'],
  ['¿Qué hago si veo un error o contenido inapropiado?', 'Usa el botón «Reportar» de cada guía o el formulario de contacto. El equipo de moderación lo revisa de forma manual.'],
]

const PASOS_ENVIO = ['Envío', 'Pendiente de revisión', 'Publicado y notificado']

function Destacados() {
  const { datos: entrevistas } = useApi('/api/contenidos?tipo=ENTREVISTA&por_pagina=1')
  const { datos: articulos } = useApi('/api/contenidos?tipo=ARTICULO&por_pagina=1')
  const { datos: historias } = useApi('/api/contenidos?categoria=historias&por_pagina=1')
  const items = [
    entrevistas?.items?.[0] && { etiqueta: 'Entrevista', c: entrevistas.items[0] },
    articulos?.items?.[0] && { etiqueta: 'Artículo técnico', c: articulos.items[0] },
    historias?.items?.[0] && { etiqueta: 'Historias de cosplayers', c: historias.items[0] },
  ].filter(Boolean)
  const vistos = new Set()
  const unicos = items.filter((i) => !vistos.has(i.c.id) && vistos.add(i.c.id))

  return (
    <section aria-labelledby="t-entrevistas" className="contenedor flex flex-wrap items-center gap-x-16 gap-y-10 py-20">
      <figure className="relative m-0 flex-[1_1_320px] max-w-[420px]">
        <div aria-hidden="true" className="absolute -left-5 -top-5 h-full w-full border border-coral" />
        <img src={armaduraPlateada} alt="" className="relative block aspect-[4/5] w-full object-cover" />
        <figcaption className="relative mt-3 text-[13px] text-lavanda">Entrevistas con cosplayers de Chile</figcaption>
      </figure>
      <div className="flex min-w-0 flex-[1.4_1_380px] flex-col gap-5">
        <h2 id="t-entrevistas" className="titulo-seccion">Entrevistas, consejos y historias</h2>
        <p className="max-w-xl text-[15px] leading-relaxed text-lavanda">
          Conversaciones con cosplayers de la escena chilena, consejos para concursos y relatos que muestran la diversidad de la comunidad local.
        </p>
        <ul>
          {unicos.map(({ etiqueta, c }) => (
            <li key={c.id}>
              <Link to={`/guias/${c.id}`} className="group flex flex-col gap-1.5 border-b border-white/16 py-4 text-white no-underline">
                <span className="etiqueta self-start">{etiqueta}</span>
                <span className="font-display text-xl font-bold group-hover:text-durazno">{c.titulo}</span>
                <span className="text-[13.5px] text-lavanda">
                  {c.autor?.nombre ? `Por ${c.autor.nombre} · ` : ''}{c.categoria?.nombre}
                </span>
              </Link>
            </li>
          ))}
          {unicos.length === 0 && <li className="text-sm text-lavanda">Pronto publicaremos entrevistas e historias.</li>}
        </ul>
        <div className="flex flex-wrap gap-3">
          <Link to="/guias?tipo=ENTREVISTA" className="boton-contorno">Ver entrevistas</Link>
          <Link to="/guias?categoria=historias" className="boton-contorno">Ver historias</Link>
        </div>
      </div>
    </section>
  )
}

// RF-02, RF-04: listado filtrable por nivel y categoría
export default function Guias() {
  useTitulo('Guías y tutoriales')
  const { usuario } = useAuth()
  const { opciones } = useMeta()
  const esFavorito = useFavoritos()
  const [params, setParams] = useSearchParams()
  const filtros = {
    nivel: params.get('nivel') || '',
    categoria: params.get('categoria') || '',
    tipo: params.get('tipo') || '',
    q: params.get('q') || '',
    pagina: Number(params.get('pagina') || 1),
  }
  const [texto, setTexto] = useState(filtros.q)
  useEffect(() => setTexto(filtros.q), [filtros.q])
  const { datos, error, cargando } = useApi(`/api/contenidos${qs({ ...filtros, por_pagina: 12 })}`)
  const { datos: categorias } = useApi('/api/categorias')

  const cambiar = (campo, valor) => {
    const p = new URLSearchParams(params)
    if (valor) p.set(campo, valor)
    else p.delete(campo)
    if (campo !== 'pagina') p.delete('pagina')
    setParams(p)
  }
  const destinoEnvio = usuario ? '/guias/publicar' : '/ingresar?siguiente=/guias/publicar'

  return (
    <div>
      {/* ---------- Encabezado ---------- */}
      <section aria-labelledby="titulo-pagina" className="contenedor flex flex-wrap items-center gap-x-16 gap-y-12 pb-16 pt-8 sm:pt-12">
        <div className="flex min-w-0 flex-[1_1_420px] flex-col gap-5">
          <Migas items={[{ a: '/', texto: 'Inicio' }, { texto: 'Guías' }]} />
          <h1 id="titulo-pagina" className="font-display text-[clamp(44px,6vw,84px)] leading-[1.02] font-bold text-white">
            Aprende cosplay paso a paso
          </h1>
          <p className="max-w-lg text-[15px] leading-relaxed text-lavanda">
            Guías en pesos chilenos, con materiales que sí se consiguen en el país. Ordenadas por nivel y por tema: desde elegir tu primer personaje
            hasta subir a un escenario.
          </p>
          <div className="flex flex-wrap gap-3">
            <a href="#enviar" className="boton-marca boton-grande">Enviar mi tutorial</a>
            <a href="#faq" className="boton-contorno boton-grande">Preguntas frecuentes</a>
          </div>
        </div>
        <div aria-hidden="true" className="relative mx-auto w-[min(340px,80%)] flex-none">
          <div className="absolute -right-10 -top-8 h-full w-full bg-linear-to-b from-coral to-uva" />
          <img src={maniqui} alt="" className="relative block aspect-square w-full object-cover" />
        </div>
      </section>

      {/* ---------- Filtros ---------- */}
      <div className="contenedor">
        <form role="search" aria-label="Filtrar guías" onSubmit={(e) => { e.preventDefault(); cambiar('q', texto.trim()) }} className="panel flex flex-col gap-4 p-5 sm:px-6">
          <GrupoChips etiqueta="Nivel" valor={filtros.nivel} onCambiar={(v) => cambiar('nivel', v)} opciones={[{ valor: '', texto: 'Todos' }, ...opciones('niveles')]} />
          <GrupoChips
            etiqueta="Categoría"
            valor={filtros.categoria}
            onCambiar={(v) => cambiar('categoria', v)}
            opciones={[{ valor: '', texto: 'Todas' }, ...(categorias || []).map((c) => ({ valor: c.slug, texto: c.nombre }))]}
          />
          <GrupoChips etiqueta="Formato" valor={filtros.tipo} onCambiar={(v) => cambiar('tipo', v)} opciones={[{ valor: '', texto: 'Todos' }, ...opciones('tipos_contenido')]} />
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/12 pt-4">
            <div className="flex min-w-0 flex-[1_1_260px] items-center gap-2">
              <label htmlFor="buscar-guias" className="sr-only">Buscar guías por palabra clave</label>
              <input
                id="buscar-guias"
                type="search"
                className="campo mt-0 max-w-sm"
                placeholder="Buscar: EVA, peluca, medidas…"
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
              />
              <button className="boton-contorno">Buscar</button>
            </div>
            <p role="status" className="text-sm text-lavanda">
              {datos && <>Mostrando <strong className="text-white">{datos.total === 1 ? '1 guía' : `${datos.total} guías`}</strong></>}
            </p>
            <p className="inline-flex items-center gap-2 text-[13px] text-lavanda">
              <Icono nombre="descargar" tamano={15} /> Las guías incluyen descarga directa con tu cuenta
            </p>
          </div>
        </form>
      </div>

      {/* ---------- Listado ---------- */}
      <section aria-label="Guías" className="contenedor py-10">
        {cargando && <Cargando />}
        <Alerta tipo="error">{error?.message}</Alerta>
        {datos && (
          <>
            {datos.items.length === 0 ? (
              <Vacio>No hay guías con esa combinación de filtros. Prueba con otra o envía tu propio tutorial.</Vacio>
            ) : (
              <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {datos.items.map((c) => (
                  <li key={c.id} className="flex">
                    <TarjetaContenido c={c} favorito={esFavorito('CONTENIDO', c.id)} />
                  </li>
                ))}
              </ul>
            )}
            <Paginacion pagina={datos.pagina} paginas={datos.paginas} onCambiar={(p) => cambiar('pagina', String(p))} />
          </>
        )}
      </section>

      {/* ---------- Errores comunes (RF-28) ---------- */}
      <section aria-labelledby="t-errores" className="mr-[7%] mt-10 bg-[linear-gradient(172deg,#c2456a_0%,#8d3a7c_58%,rgba(40,18,84,.35)_100%)] px-gutter py-12">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-6">
          <h2 id="t-errores" className="titulo-seccion">Errores comunes y cómo evitarlos</h2>
          <p className="max-w-sm text-sm text-white">
            Los fallos más frecuentes al confeccionar o estilizar un traje, y cómo evitarlos.{' '}
            <Link to="/guias?categoria=errores-comunes" className="font-bold text-white underline">Ver guías</Link>
          </p>
        </div>
        <ol className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {ERRORES.map(([t, d], i) => (
            <li key={t}>
              <span aria-hidden="true" className="font-display text-[40px] leading-none font-bold text-rosado">{String(i + 1).padStart(2, '0')}</span>
              <h3 className="mt-2 text-base font-bold text-white">{t}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/90">{d}</p>
            </li>
          ))}
        </ol>
      </section>

      <Destacados />

      {/* ---------- Seguridad en eventos (RF-39) ---------- */}
      <section aria-labelledby="t-seguridad" className="contenedor pb-20">
        <h2 id="t-seguridad" className="titulo-seccion">Seguridad en eventos</h2>
        <p className="mt-3 max-w-xl text-[15px] text-lavanda">Consejos, artículos e instrucciones para ir a un evento con tranquilidad.</p>
        <ul className="mt-8 grid gap-5 md:grid-cols-3">
          {SEGURIDAD.map((s) => (
            <li key={s.titulo}>
              <Link to="/seguridad#consejos" className="panel group flex h-full flex-col gap-3 p-6 text-white no-underline hover:border-coral">
                <Icono nombre={s.icono} tamano={30} grosor={1.5} className="text-durazno" />
                <span className="font-display text-2xl font-bold">{s.titulo}</span>
                <span className="text-sm leading-relaxed text-lavanda">{s.texto}</span>
                <span className="mt-auto inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[.14em] text-durazno">
                  Leer consejos <Icono nombre="derecha" tamano={14} grosor={2.2} />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* ---------- FAQ y envío ---------- */}
      <div className="contenedor grid gap-x-16 gap-y-14 pb-24 lg:grid-cols-2">
        <section id="faq" aria-labelledby="t-faq" className="scroll-mt-6">
          <h2 id="t-faq" className="titulo-seccion">Preguntas frecuentes</h2>
          <p className="mb-6 mt-3 text-[15px] text-lavanda">Preguntas frecuentes sobre el cosplay y el uso de la plataforma.</p>
          <Acordeon items={FAQ.map(([titulo, contenido]) => ({ titulo, contenido }))} />
        </section>

        <section id="enviar" aria-labelledby="t-enviar" className="panel scroll-mt-6 p-6 sm:p-8">
          <h2 id="t-enviar" className="font-display text-[clamp(28px,3vw,38px)] leading-tight font-bold text-white">Envía tu propio tutorial</h2>
          <p className="mt-3 text-[15px] leading-relaxed text-lavanda">
            Necesitas haber iniciado sesión. Tu tutorial se guarda como «pendiente de revisión» y el equipo de moderación lo revisa antes de
            publicarlo. Puedes incluir texto, pasos, materiales, una imagen (JPG, PNG o WebP de hasta 5 MB) y un video de YouTube o Vimeo.
          </p>
          <ol className="my-7 grid gap-3 sm:grid-cols-3" aria-label="Cómo se publica un tutorial">
            {PASOS_ENVIO.map((p, i) => (
              <li key={p} className="flex items-center gap-3 sm:flex-col sm:items-start">
                <span aria-hidden="true" className={`inline-flex size-9 items-center justify-center rounded-full font-bold ${i === 0 ? 'bg-linear-120 from-coral to-fucsia text-tinta-oscura' : 'border border-white/40 text-white'}`}>
                  {i + 1}
                </span>
                <span className="text-sm text-white">{p}</span>
              </li>
            ))}
          </ol>
          <Link to={destinoEnvio} className="boton-marca boton-grande">
            {usuario ? 'Escribir mi tutorial' : 'Inicia sesión para enviar'}
          </Link>
          <p className="mt-3 text-[13px] text-lavanda">Recibirás una notificación cuando sea revisado.</p>
        </section>
      </div>
    </div>
  )
}
