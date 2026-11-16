import { Link } from 'react-router-dom'
import { useMeta } from '../../contexto/MetaContext'
import useApi from '../../components/useApi'
import { formatoFecha } from '../../components/ui'

export const COLOR_ESTADO = {
  PENDIENTE: 'bg-estrella text-[#2a1c00]',
  PUBLICADO: 'bg-nivel-principiante text-[#06281a]',
  RECHAZADO: 'bg-peligro text-[#2a0606]',
  OCULTO: 'bg-white/70 text-tinta-oscura',
}

export default function MisEnvios() {
  const { etiqueta } = useMeta()
  const { datos } = useApi('/api/contenidos/mios')
  return (
    <section id="mis-envios" className="panel scroll-mt-6 p-6" aria-labelledby="titulo-envios">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="titulo-envios" className="font-display text-2xl font-bold text-white">Mis envíos</h2>
        <Link to="/guias/publicar" className="boton-contorno">Enviar un tutorial</Link>
      </div>
      {!datos || datos.length === 0 ? (
        <p className="mt-3 text-sm text-lavanda">Todavía no envías tutoriales.</p>
      ) : (
        <ul className="mt-4">
          {datos.map((c) => (
            <li key={c.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-white/12 py-3 last:border-b-0">
              <div className="min-w-0">
                <Link to={`/guias/${c.id}`} className="font-bold text-white no-underline hover:text-durazno">{c.titulo}</Link>
                <p className="text-[13px] text-lavanda">Enviado el {formatoFecha(c.created_at)}</p>
              </div>
              <span className={`insignia ${COLOR_ESTADO[c.estado]}`}>{etiqueta('estados_publicacion', c.estado)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
