import { Suspense, lazy, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { qs } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import { useMeta } from '../../contexto/MetaContext'
import BotonFavorito from '../../components/BotonFavorito'
import Icono from '../../components/diseno/Icono'
import Pestanas from '../../components/diseno/Pestanas'
import useApi from '../../components/useApi'
import useFavoritos from '../../components/useFavoritos'
import { Alerta, Cargando, EncabezadoPagina, Estrellas, GrupoChips, Paginacion, Vacio, formatoCLP, useTitulo } from '../../components/ui'
import { Avatar, Contacto, Precios, Resenas, especialidadDe, modalidadDe, ubicacionDe } from './Ficha'
import MapaEsquematico, { REGION_CORTA, regionesDesdePuntos } from './MapaEsquematico'

const MapaChile = lazy(() => import('./MapaChile'))

const PESTANAS = [
  { valor: 'PROVEEDOR', texto: 'Profesionales' },
  { valor: 'TIENDA', texto: 'Tiendas · dónde comprar' },
  { valor: 'COMUNIDAD', texto: 'Comunidades por región' },
]
const ESCRITORIO = '(min-width: 1280px)'

function useEscritorio() {
  const [es, setEs] = useState(() => Boolean(window.matchMedia?.(ESCRITORIO).matches))
  useEffect(() => {
    const m = window.matchMedia?.(ESCRITORIO)
    if (!m?.addEventListener) return
    const alCambiar = () => setEs(m.matches)
    m.addEventListener('change', alCambiar)
    return () => m.removeEventListener('change', alCambiar)
  }, [])
  return es
}

function TarjetaItem({ i, seleccionado, onVer }) {
  const { etiqueta } = useMeta()
  const modalidad = modalidadDe(i)
  return (
    <article
      className={`flex flex-wrap items-center gap-x-5 gap-y-3 border p-[18px] transition-colors ${
        seleccionado ? 'border-coral bg-coral/12' : 'border-white/14 bg-white/5'
      }`}
    >
      <Avatar i={i} destacado={seleccionado} />
      <div className="min-w-0 flex-[1_1_240px]">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <h3 className="font-display text-[22px] leading-tight font-bold text-white">
            <Link to={`/directorio/${i.id}`} className="text-white no-underline hover:text-durazno">{i.nombre}</Link>
          </h3>
          {i.tipo !== 'COMUNIDAD' && <Estrellas valor={i.promedio} total={i.total_resenas} />}
        </div>
        <p className="mt-1 text-sm text-white">{especialidadDe(i, etiqueta)}</p>
        <p className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-lavanda">
          <span className="inline-flex items-center gap-1.5"><Icono nombre="ubicacion" tamano={14} /> {ubicacionDe(i, etiqueta)}</span>
          {modalidad && <span>{modalidad}</span>}
          {i.precio_desde != null && <strong className="text-white">Desde {formatoCLP(i.precio_desde)} CLP</strong>}
        </p>
      </div>
      <button
        type="button"
        onClick={onVer}
        aria-label={`${seleccionado ? 'Ficha abierta' : 'Ver ficha'}: ${i.nombre}`}
        aria-pressed={seleccionado}
        className={seleccionado ? 'boton-marca' : 'boton-contorno'}
      >
        {seleccionado ? 'Ficha abierta' : 'Ver ficha'}
      </button>
    </article>
  )
}

// Ficha lateral (pantallas anchas): vista previa del detalle con contacto, precios y reseñas
function FichaLateral({ id, favorito }) {
  const { etiqueta } = useMeta()
  const { datos: i, error, cargando, recargar } = useApi(id ? `/api/directorio/${id}` : null)
  if (!id) return null
  if (cargando && !i) return <div className="panel p-6"><Cargando texto="Cargando ficha…" /></div>
  if (error) return <Alerta tipo="error">{error.message}</Alerta>
  if (!i) return null
  return (
    <aside aria-labelledby="t-ficha" className="panel sticky top-4 flex flex-col gap-5 p-6">
      <div className="flex items-center gap-4">
        <Avatar i={i} destacado tamano="size-[60px]" />
        <div className="min-w-0">
          <p className="sobretitulo">{especialidadDe(i, etiqueta)}</p>
          <h2 id="t-ficha" className="font-display text-2xl font-bold text-white">{i.nombre}</h2>
        </div>
      </div>
      <p className="text-sm leading-relaxed text-lavanda">
        {i.descripcion} {ubicacionDe(i, etiqueta)}
        {modalidadDe(i) ? ` · ${modalidadDe(i)}.` : ''}
      </p>
      {i.portafolio?.length > 0 && (
        <section aria-label="Portafolio">
          <h3 className="sobretitulo mb-2 text-lavanda">Portafolio</h3>
          <ul className="grid grid-cols-3 gap-2">
            {i.portafolio.slice(0, 3).map((img, k) => (
              <li key={k}><img src={img.url} alt={img.alt} className="aspect-square w-full object-cover" loading="lazy" /></li>
            ))}
          </ul>
        </section>
      )}
      <Precios i={i} />
      <Contacto i={i} />
      <div className="flex flex-wrap gap-3">
        <BotonFavorito tipo="DIRECTORIO" objetoId={i.id} inicial={favorito || i.es_favorito} />
        <Link to={`/directorio/${i.id}`} className="boton-contorno">Ficha completa</Link>
      </div>
      {i.tipo !== 'COMUNIDAD' && (
        <div className="border-t border-white/12 pt-5">
          <Resenas i={i} recargar={recargar} limite={3} />
        </div>
      )}
    </aside>
  )
}

function TarjetaComunidad({ i }) {
  const { etiqueta } = useMeta()
  return (
    <article className="flex h-full flex-col border border-white/14 bg-white/5">
      {i.imagen_url ? (
        <img src={i.imagen_url} alt={i.imagen_alt || ''} className="aspect-[16/10] w-full object-cover" loading="lazy" />
      ) : (
        <div aria-hidden="true" className="aspect-[16/10] w-full bg-linear-135 from-ciruela to-uva" />
      )}
      <div className="flex flex-1 flex-col gap-2 p-5">
        <h3 className="font-display text-xl font-bold text-white">{i.nombre}</h3>
        <p className="text-[13px] text-lavanda">
          Región {REGION_CORTA[i.region] || etiqueta('regiones', i.region)}{i.plataforma ? ` · ${i.plataforma}` : ''}
        </p>
        <p className="line-clamp-3 text-sm text-lavanda">{i.descripcion}</p>
        <Link to={`/directorio/${i.id}`} className="boton-texto mt-auto self-start no-underline">
          Ver comunidad <Icono nombre="derecha" tamano={14} grosor={2.2} />
          <span className="sr-only">: {i.nombre}</span>
        </Link>
      </div>
    </article>
  )
}

// RF-11 a RF-14, RF-33, RF-34
export default function Directorio() {
  useTitulo('Directorio')
  const { usuario } = useAuth()
  const { opciones, etiqueta } = useMeta()
  const esFavorito = useFavoritos()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const tipo = PESTANAS.some((p) => p.valor === params.get('tipo')) ? params.get('tipo') : 'PROVEEDOR'
  const f = {
    region: params.get('region') || '',
    especialidad: params.get('especialidad') || '',
    tipo_producto: params.get('tipo_producto') || '',
    alcance: params.get('alcance') || '',
    q: params.get('q') || '',
    pagina: Number(params.get('pagina') || 1),
  }
  const vista = params.get('vista') === 'mapa' ? 'mapa' : 'lista'
  const filtrosApi = {
    tipo,
    region: f.region,
    especialidad: tipo === 'PROVEEDOR' ? f.especialidad : '',
    tipo_producto: tipo === 'TIENDA' ? f.tipo_producto : '',
  }
  const [texto, setTexto] = useState(f.q)
  useEffect(() => setTexto(f.q), [f.q])
  const lista = useApi(`/api/directorio${qs({ ...filtrosApi, alcance: tipo === 'TIENDA' ? f.alcance : '', q: f.q, pagina: f.pagina, por_pagina: 12 })}`)
  const puntos = useApi(`/api/directorio/mapa${qs({ tipo })}`)
  const puntosFiltrados = useApi(vista === 'mapa' ? `/api/directorio/mapa${qs(filtrosApi)}` : null)
  const escritorio = useEscritorio()
  const [seleccion, setSeleccion] = useState(null)
  const items = lista.datos?.items || []
  const seleccionado = items.some((i) => i.id === seleccion) ? seleccion : items[0]?.id

  const cambiar = (cambios) => {
    const p = new URLSearchParams(params)
    for (const [k, v] of Object.entries(cambios)) {
      if (v) p.set(k, v)
      else p.delete(k)
    }
    if (!('pagina' in cambios)) p.delete('pagina')
    setParams(p)
  }
  const verFicha = (id) => {
    if (escritorio) setSeleccion(id)
    else navigate(`/directorio/${id}`)
  }

  const regionesPresentes = regionesDesdePuntos(puntos.datos || []).map((r) => r.region)
  const subtipos = tipo === 'PROVEEDOR' ? opciones('especialidades') : tipo === 'TIENDA' ? opciones('tipos_producto') : []
  const campoSubtipo = tipo === 'PROVEEDOR' ? 'especialidad' : 'tipo_producto'
  const esComunidad = tipo === 'COMUNIDAD'

  return (
    <div className="pb-0">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { texto: 'Directorio' }]}
        titulo={<>Dónde comprar<br className="hidden sm:block" /> y a quién contratar</>}
        bajada="Cosmakers, sastrerías, fotógrafos y tiendas con envío a Chile, filtrables por región y especialidad. Esta plataforma es un catálogo de contacto directo: no procesa pagos."
      >
        <Pestanas
          className="mt-10"
          etiqueta="Secciones del directorio"
          idPanel="panel-directorio"
          pestanas={PESTANAS}
          valor={tipo}
          onCambiar={(v) => cambiar({ tipo: v, especialidad: '', tipo_producto: '', alcance: '' })}
        />
      </EncabezadoPagina>

      <div id="panel-directorio" role="tabpanel" aria-labelledby={`panel-directorio-tab-${tipo}`} className="contenedor py-8">
        <div className={`grid grid-cols-1 items-start gap-6 lg:grid-cols-[15rem_minmax(0,1fr)] ${!esComunidad && vista === 'lista' ? 'xl:grid-cols-[15rem_minmax(0,1fr)_23rem]' : ''}`}>
          <MapaEsquematico
            puntos={puntos.datos || []}
            region={f.region}
            onRegion={(r) => cambiar({ region: r })}
            onDetallado={() => cambiar({ vista: vista === 'mapa' ? '' : 'mapa' })}
          />

          <div className="min-w-0">
            <form
              role="search"
              aria-label="Filtrar directorio"
              onSubmit={(e) => {
                e.preventDefault()
                cambiar({ q: texto.trim() })
              }}
              className="panel flex flex-col gap-4 p-5"
            >
              <div className="flex items-center gap-2">
                <label htmlFor="buscar-directorio" className="sr-only">Buscar en el directorio</label>
                <div className="flex min-h-11 flex-1 items-center gap-2.5 rounded-campo border border-white/30 bg-noche/60 px-3.5 focus-within:border-coral">
                  <Icono nombre="buscar" tamano={17} className="text-lavanda" />
                  <input
                    id="buscar-directorio"
                    type="search"
                    value={texto}
                    onChange={(e) => setTexto(e.target.value)}
                    placeholder="Busca por nombre, servicio o ciudad"
                    className="min-w-0 flex-1 bg-transparent py-2 text-white outline-none"
                  />
                </div>
                <button className="boton-contorno">Buscar</button>
              </div>
              <GrupoChips
                etiqueta="Región"
                valor={f.region}
                onCambiar={(v) => cambiar({ region: v })}
                opciones={[
                  { valor: '', texto: 'Todas' },
                  ...[...new Set([...regionesPresentes, ...(f.region ? [f.region] : [])])].map((r) => ({
                    valor: r,
                    texto: REGION_CORTA[r] || etiqueta('regiones', r),
                  })),
                ]}
              />
              {subtipos.length > 0 && (
                <GrupoChips
                  etiqueta="Tipo"
                  valor={f[campoSubtipo]}
                  onCambiar={(v) => cambiar({ [campoSubtipo]: v })}
                  opciones={[{ valor: '', texto: 'Todas' }, ...subtipos]}
                />
              )}
              {tipo === 'TIENDA' && (
                <div>
                  <button
                    type="button"
                    className="chip-filtro"
                    aria-pressed={f.alcance === 'INTERNACIONAL'}
                    onClick={() => cambiar({ alcance: f.alcance === 'INTERNACIONAL' ? '' : 'INTERNACIONAL' })}
                  >
                    Internacionales con envío a Chile
                  </button>
                </div>
              )}
              <p role="status" className="border-t border-white/12 pt-3 text-sm text-lavanda">
                {lista.datos && (
                  <>Mostrando <strong className="text-white">{lista.datos.total === 1 ? '1 resultado' : `${lista.datos.total} resultados`}</strong></>
                )}
              </p>
            </form>

            {vista === 'mapa' ? (
              <section aria-label="Mapa detallado" className="mt-5">
                {puntosFiltrados.cargando && <Cargando texto="Cargando mapa…" />}
                <Alerta tipo="error">{puntosFiltrados.error?.message}</Alerta>
                {puntosFiltrados.datos && (
                  <Suspense fallback={<Cargando texto="Cargando mapa…" />}>
                    <MapaChile puntos={puntosFiltrados.datos} />
                  </Suspense>
                )}
                <button type="button" className="boton-contorno mt-4" onClick={() => cambiar({ vista: '' })}>
                  Volver a la lista
                </button>
              </section>
            ) : (
              <section aria-label="Resultados" className="mt-5">
                {lista.cargando && <Cargando />}
                <Alerta tipo="error">{lista.error?.message}</Alerta>
                {lista.datos && items.length === 0 && (
                  <Vacio>No hay resultados con esos filtros. Prueba con otra región o especialidad.</Vacio>
                )}
                {esComunidad ? (
                  <>
                    <p className="mb-4 text-sm text-lavanda">Grupos y comunidades presenciales por región, con enlaces a sus redes oficiales.</p>
                    <ul className="grid gap-5 sm:grid-cols-2 2xl:grid-cols-3">
                      {items.map((i) => <li key={i.id}><TarjetaComunidad i={i} /></li>)}
                    </ul>
                  </>
                ) : (
                  <ul className="space-y-3">
                    {items.map((i) => (
                      <li key={i.id}>
                        <TarjetaItem i={i} seleccionado={escritorio && i.id === seleccionado} onVer={() => verFicha(i.id)} />
                      </li>
                    ))}
                  </ul>
                )}
                {lista.datos && (
                  <Paginacion pagina={lista.datos.pagina} paginas={lista.datos.paginas} onCambiar={(p) => cambiar({ pagina: String(p) })} />
                )}
              </section>
            )}
          </div>

          {!esComunidad && vista === 'lista' && (
            <div className="hidden xl:block">
              <FichaLateral id={seleccionado} favorito={esFavorito('DIRECTORIO', seleccionado)} />
            </div>
          )}
        </div>
      </div>

      <section aria-labelledby="t-ofreces" className="mr-[7%] mt-10 bg-[linear-gradient(172deg,#c2456a_0%,#8d3a7c_58%,rgba(40,18,84,.35)_100%)] px-gutter py-12">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="max-w-2xl">
            <h2 id="t-ofreces" className="font-display text-[clamp(28px,3vw,40px)] leading-tight font-bold text-white">¿Ofreces servicios o vendes materiales?</h2>
            <p className="mt-3 text-[15px] leading-relaxed text-white">
              Crea tu cuenta y activa tu perfil en el directorio público. Después puedes completar tu ficha con servicios, precios y portafolio.
            </p>
          </div>
          <Link to={usuario ? '/perfil' : '/registro?tipo=COSMAKER'} className="boton-claro boton-grande">
            {usuario ? 'Activar mi ficha' : 'Registrar mi taller o tienda'}
          </Link>
        </div>
      </section>
    </div>
  )
}
