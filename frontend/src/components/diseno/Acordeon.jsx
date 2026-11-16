import { useId, useState } from 'react'

// Acordeón accesible (botón con aria-expanded que controla una región). Uno abierto a la vez.
export default function Acordeon({ items, inicial = 0, nivelTitulo = 3 }) {
  const id = useId()
  const [abierto, setAbierto] = useState(inicial)
  const Titulo = `h${nivelTitulo}`
  return (
    <div>
      {items.map((it, i) => {
        const abierta = abierto === i
        return (
          <div key={it.titulo}>
            <Titulo className="m-0">
              <button
                type="button"
                id={`${id}-b${i}`}
                aria-expanded={abierta}
                aria-controls={`${id}-p${i}`}
                onClick={() => setAbierto(abierta ? -1 : i)}
                className="flex min-h-14 w-full items-center justify-between gap-4 border-b border-white/18 px-1 py-3 text-left text-base font-bold text-white"
              >
                <span className="flex flex-wrap items-center gap-3">
                  {it.titulo}
                  {it.etiqueta && <span className="etiqueta text-xs font-medium">{it.etiqueta}</span>}
                </span>
                <span aria-hidden="true" className="text-xl text-durazno">{abierta ? '–' : '+'}</span>
              </button>
            </Titulo>
            <div id={`${id}-p${i}`} role="region" aria-labelledby={`${id}-b${i}`} hidden={!abierta} className="px-1 pb-5 pt-3 text-[15px] leading-relaxed text-lavanda">
              {it.contenido}
            </div>
          </div>
        )
      })}
    </div>
  )
}
