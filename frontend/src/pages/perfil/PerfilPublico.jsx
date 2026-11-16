import { useParams } from 'react-router-dom'
import { useMeta } from '../../contexto/MetaContext'
import Icono from '../../components/diseno/Icono'
import useApi from '../../components/useApi'
import { Alerta, Cargando, Migas, useTitulo } from '../../components/ui'
import NoEncontrado from '../NoEncontrado'

// RF-08: biografía, portafolio, redes y región (solo si la persona activó su perfil público, RF-10)
export default function PerfilPublico() {
  const { id } = useParams()
  const { etiqueta } = useMeta()
  const { datos, error, cargando } = useApi(`/api/perfil/${id}`)
  useTitulo(datos?.nombre || 'Perfil')
  if (cargando) return <div className="contenedor"><Cargando /></div>
  if (error?.status === 404 || error?.status === 422) return <NoEncontrado titulo="Perfil no disponible" texto="Este perfil no existe o no es público." />
  if (error) return <div className="contenedor py-10"><Alerta tipo="error">{error.message}</Alerta></div>
  if (!datos) return null
  const p = datos.perfil
  return (
    <article className="contenedor max-w-5xl pb-24 pt-8 sm:pt-12">
      <Migas items={[{ a: '/', texto: 'Inicio' }, { a: '/comunidad', texto: 'Comunidad' }, { texto: datos.nombre }]} />
      <header className="flex flex-wrap items-center gap-6">
        <span aria-hidden="true" className="inline-flex size-28 flex-none items-center justify-center rounded-full border-2 border-coral bg-linear-135 from-coral to-fucsia font-display text-5xl font-bold text-tinta-oscura">
          {datos.nombre.charAt(0).toUpperCase()}
        </span>
        <div className="min-w-0">
          <p className="sobretitulo">{etiqueta('tipos_perfil', p.tipo_perfil)}</p>
          <h1 className="font-display text-[clamp(38px,5vw,64px)] leading-[1.05] font-bold text-white">{datos.nombre}</h1>
          <p className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-lavanda">
            {p.region && <span className="inline-flex items-center gap-1.5"><Icono nombre="ubicacion" tamano={15} /> {etiqueta('regiones', p.region)}</span>}
            {p.especialidad && <span>{p.especialidad}</span>}
            {p.disponibilidad && <span>Disponibilidad: {p.disponibilidad}</span>}
          </p>
        </div>
      </header>
      {p.biografia && <p className="mt-8 max-w-3xl whitespace-pre-line text-lg leading-relaxed text-tinta">{p.biografia}</p>}
      {p.redes_sociales?.length > 0 && (
        <ul className="mt-6 flex flex-wrap gap-3">
          {p.redes_sociales.map((r) => (
            <li key={r.url}>
              <a href={r.url} className="boton-contorno" target="_blank" rel="noreferrer">
                {r.red} <Icono nombre="externo" tamano={13} grosor={2.2} />
                <span className="sr-only"> (se abre en otra pestaña)</span>
              </a>
            </li>
          ))}
        </ul>
      )}
      {p.portafolio?.length > 0 && (
        <section className="mt-12" aria-labelledby="t-port">
          <h2 id="t-port" className="mb-5 font-display text-3xl font-bold text-white">Portafolio</h2>
          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {p.portafolio.map((img, k) => <li key={k}><img src={img.url} alt={img.alt} className="aspect-square w-full object-cover" loading="lazy" /></li>)}
          </ul>
        </section>
      )}
    </article>
  )
}
