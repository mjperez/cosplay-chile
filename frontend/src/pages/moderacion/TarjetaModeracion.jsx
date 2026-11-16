import { Link } from 'react-router-dom'
import Icono from '../../components/diseno/Icono'

// Tarjeta de un elemento por revisar (diseño): título, metadatos en coral, autor, enlace y acciones
export default function TarjetaModeracion({ titulo, meta, autor, enlace, textoEnlace = 'Ver contenido completo', etiquetas, children }) {
  return (
    <li className="panel p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          {etiquetas && <div className="mb-2 flex flex-wrap gap-2">{etiquetas}</div>}
          <h3 className="font-display text-xl leading-tight font-bold text-white">{titulo}</h3>
          <p className="mt-1 flex flex-wrap gap-x-3 text-[13px]">
            {meta && <span className="font-bold text-coral">{meta}</span>}
            {autor && <span className="text-lavanda">{autor}</span>}
          </p>
        </div>
        {enlace && (
          <Link to={enlace} className="inline-flex min-h-11 items-center gap-1.5 text-[13px] text-white underline underline-offset-[3px] hover:text-durazno">
            <Icono nombre="ojo" tamano={15} /> {textoEnlace}
            <span className="sr-only">: {titulo}</span>
          </Link>
        )}
      </div>
      {children}
    </li>
  )
}
