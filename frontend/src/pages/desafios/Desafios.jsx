import { Link } from 'react-router-dom'
import Icono from '../../components/diseno/Icono'
import useApi from '../../components/useApi'
import { Alerta, Cargando, EncabezadoPagina, Vacio, useTitulo } from '../../components/ui'

export const nombreMes = (mes, anio) =>
  new Date(anio, mes - 1, 1).toLocaleDateString('es-CL', { month: 'long', year: 'numeric' })

// RF-36: desafíos mensuales con participación comunitaria
export default function Desafios() {
  useTitulo('Desafíos mensuales')
  const { datos, error, cargando } = useApi('/api/desafios')
  const abiertos = datos?.filter((d) => d.abierto) || []
  const cerrados = datos?.filter((d) => !d.abierto) || []
  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { a: '/comunidad', texto: 'Comunidad' }, { texto: 'Desafíos' }]}
        titulo="Desafíos mensuales"
        bajada="Cada mes un reto para crear, aprender y compartir. Sube tu foto con créditos y participa."
      />
      <div className="contenedor mt-10">
        {cargando && <Cargando />}
        <Alerta tipo="error">{error?.message}</Alerta>
        {datos?.length === 0 && <Vacio>Todavía no hay desafíos.</Vacio>}
        {abiertos.map((d) => (
          <section key={d.id} className="mb-10 bg-[linear-gradient(160deg,#c2456a_0%,#8d3a7c_60%,#3a1a6a_100%)] px-[clamp(20px,4vw,56px)] py-12" aria-labelledby={`d-${d.id}`}>
            <p className="text-xs font-bold uppercase tracking-[.2em] text-rosado">Desafío de {nombreMes(d.mes, d.anio)}</p>
            <h2 id={`d-${d.id}`} className="mt-3 font-display text-[clamp(32px,3.6vw,48px)] leading-[1.08] font-bold text-white">{d.titulo}</h2>
            <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-white">{d.descripcion}</p>
            <p className="mt-3 inline-flex items-center gap-2 text-sm text-white">
              <Icono nombre="personas" tamano={16} /> {d.participaciones === 1 ? '1 participación' : `${d.participaciones} participaciones`}
            </p>
            <div className="mt-6">
              <Link to={`/desafios/${d.id}`} className="boton-claro boton-grande">Ver y participar</Link>
            </div>
          </section>
        ))}
        {cerrados.length > 0 && (
          <section aria-labelledby="t-anteriores">
            <h2 id="t-anteriores" className="titulo-seccion mb-6">Desafíos anteriores</h2>
            <ul className="grid gap-4 sm:grid-cols-2">
              {cerrados.map((d) => (
                <li key={d.id} className="panel p-6">
                  <p className="sobretitulo first-letter:uppercase">{nombreMes(d.mes, d.anio)}</p>
                  <h3 className="mt-2 font-display text-2xl font-bold">
                    <Link to={`/desafios/${d.id}`} className="text-white no-underline hover:text-durazno">{d.titulo}</Link>
                  </h3>
                  <p className="mt-3 inline-flex items-center gap-2 text-sm text-lavanda">
                    <Icono nombre="trofeo" tamano={16} className="text-estrella" />
                    {d.ganador ? `Ganó ${d.ganador.nombre}` : 'Sin ganador'}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  )
}
