import { Link, useParams } from 'react-router-dom'
import { useMeta } from '../../contexto/MetaContext'
import BotonFavorito from '../../components/BotonFavorito'
import BotonReportar from '../../components/BotonReportar'
import CompartirRedes from '../../components/CompartirRedes'
import Icono from '../../components/diseno/Icono'
import useApi from '../../components/useApi'
import { Alerta, Cargando, Estrellas, Migas, useTitulo } from '../../components/ui'
import NoEncontrado from '../NoEncontrado'
import { Avatar, Contacto, Precios, Resenas, especialidadDe, modalidadDe, ubicacionDe } from './Ficha'

// RF-32: ficha con nombre, servicios, contacto, portafolio, precios y región; RF-19 reseñas
export default function DirectorioDetalle() {
  const { id } = useParams()
  const { etiqueta } = useMeta()
  const { datos: i, error, cargando, recargar } = useApi(`/api/directorio/${id}`)
  useTitulo(i?.nombre || 'Directorio')

  if (cargando && !i) return <div className="contenedor"><Cargando /></div>
  if (error?.status === 404 || error?.status === 422) return <NoEncontrado titulo="Ficha no encontrada" />
  if (error) return <div className="contenedor py-10"><Alerta tipo="error">{error.message}</Alerta></div>
  if (!i) return null

  const pestana = { PROVEEDOR: 'Profesionales', TIENDA: 'Tiendas', COMUNIDAD: 'Comunidades' }[i.tipo]
  return (
    <article className="contenedor pb-24 pt-8 sm:pt-12">
      <Migas items={[{ texto: 'Inicio', a: '/' }, { texto: 'Directorio', a: '/directorio' }, { texto: pestana, a: `/directorio?tipo=${i.tipo}` }, { texto: i.nombre }]} />
      <header className="flex flex-wrap items-center gap-6">
        <Avatar i={i} destacado tamano="size-28" />
        <div className="min-w-0 flex-1">
          <p className="sobretitulo">{especialidadDe(i, etiqueta)}</p>
          <h1 className="font-display text-[clamp(38px,5vw,64px)] leading-[1.05] font-bold text-white">{i.nombre}</h1>
          <p className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-lavanda">
            <span className="inline-flex items-center gap-1.5">
              <Icono nombre="ubicacion" tamano={15} />
              {[i.direccion, ubicacionDe(i, etiqueta)].filter(Boolean).join(', ')}
            </span>
            {modalidadDe(i) && <span>{modalidadDe(i)}</span>}
            {i.tipo !== 'COMUNIDAD' && <Estrellas valor={i.promedio} total={i.total_resenas} />}
          </p>
        </div>
      </header>

      <div className="mt-10 grid items-start gap-10 lg:grid-cols-[1fr_22rem]">
        <div className="min-w-0">
          <p className="whitespace-pre-line text-lg leading-relaxed text-tinta">{i.descripcion}</p>
          {i.portafolio?.length > 0 && (
            <section className="mt-10" aria-labelledby="t-portafolio">
              <h2 id="t-portafolio" className="mb-4 font-display text-3xl font-bold text-white">Portafolio</h2>
              <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {i.portafolio.map((img, k) => (
                  <li key={k}><img src={img.url} alt={img.alt} className="aspect-square w-full object-cover" loading="lazy" /></li>
                ))}
              </ul>
            </section>
          )}
          {i.tipo !== 'COMUNIDAD' && (
            <div className="panel mt-10 p-6">
              <Resenas i={i} recargar={recargar} />
            </div>
          )}
        </div>

        <aside aria-label="Contacto y precios" className="panel flex flex-col gap-5 p-6 lg:sticky lg:top-4">
          <Precios i={i} />
          <Contacto i={i} />
          {i.perfil_usuario_id && (
            <Link to={`/personas/${i.perfil_usuario_id}`} className="enlace-claro text-sm">Ver perfil de la persona</Link>
          )}
          <div className="flex flex-wrap items-center gap-3 border-t border-white/12 pt-5">
            <BotonFavorito tipo="DIRECTORIO" objetoId={i.id} inicial={i.es_favorito} />
            <CompartirRedes titulo={i.nombre} ruta={`/directorio/${i.id}`} />
          </div>
          <BotonReportar tipo="DIRECTORIO" objetoId={i.id} />
          <p className="text-xs text-lavanda">Cosplay Chile no procesa pagos: el contacto y la compra son directos con el proveedor.</p>
        </aside>
      </div>
    </article>
  )
}
