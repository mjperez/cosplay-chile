import { Link } from 'react-router-dom'
import { useMeta } from '../../contexto/MetaContext'
import BotonFavorito from '../../components/BotonFavorito'
import CompartirRedes from '../../components/CompartirRedes'
import Icono from '../../components/diseno/Icono'
import { InsigniaNivel } from '../../components/diseno/Insignias'

// Tarjeta de guía del diseño: imagen con nivel, categoría, título, formato y acciones
export default function TarjetaContenido({ c, favorito = false }) {
  const { etiqueta } = useMeta()
  return (
    <article className="flex w-full flex-col border border-white/14 bg-white/5">
      <div className="relative">
        {c.imagen_url ? (
          <img src={c.imagen_url} alt={c.imagen_alt || ''} className="aspect-[4/3] w-full object-cover" loading="lazy" />
        ) : (
          <div className="aspect-[4/3] w-full bg-linear-135 from-ciruela to-uva" aria-hidden="true" />
        )}
        <InsigniaNivel nivel={c.nivel} className="absolute left-3.5 top-3.5" />
      </div>
      <div className="flex flex-1 flex-col gap-2 p-[15px]">
        <p className="sobretitulo text-[11px]">{c.categoria?.nombre}</p>
        <h3 className="font-display text-xl leading-tight font-bold text-white">
          <Link to={`/guias/${c.id}`} className="text-white no-underline hover:text-durazno">
            {c.titulo}
          </Link>
        </h3>
        <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-lavanda">
          {c.tipo !== 'GUIA' && <span>{etiqueta('tipos_contenido', c.tipo)}</span>}
          <span className="inline-flex items-center gap-1.5"><Icono nombre="descargar" tamano={14} /> Descargable</span>
          {c.autor?.nombre && <span>por {c.autor.nombre}</span>}
        </p>
        <div className="mt-auto flex items-center justify-between gap-2 pt-3">
          <Link to={`/guias/${c.id}`} className="boton-texto no-underline" aria-label={`Leer guía: ${c.titulo}`}>
            Leer guía <Icono nombre="derecha" tamano={14} grosor={2.2} />
          </Link>
          <span className="flex gap-2">
            <BotonFavorito variante="icono" tipo="CONTENIDO" objetoId={c.id} inicial={favorito} nombre={c.titulo} />
            <CompartirRedes titulo={c.titulo} ruta={`/guias/${c.id}`} />
          </span>
        </div>
      </div>
    </article>
  )
}
