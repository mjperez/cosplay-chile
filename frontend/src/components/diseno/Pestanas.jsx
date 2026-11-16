import { useRef } from 'react'

// Pestañas accesibles (patrón ARIA tabs): flechas, Inicio y Fin mueven el foco y activan la pestaña.
// El panel lo pinta quien la usa, con id={idPanel}, role="tabpanel" y aria-labelledby={`${idPanel}-tab-${valor}`}.
export default function Pestanas({ pestanas, valor, onCambiar, idPanel, etiqueta, className = '' }) {
  const refs = useRef({})
  const mover = (e, i) => {
    let j = null
    if (e.key === 'ArrowRight') j = (i + 1) % pestanas.length
    else if (e.key === 'ArrowLeft') j = (i - 1 + pestanas.length) % pestanas.length
    else if (e.key === 'Home') j = 0
    else if (e.key === 'End') j = pestanas.length - 1
    if (j === null) return
    e.preventDefault()
    onCambiar(pestanas[j].valor)
    refs.current[pestanas[j].valor]?.focus()
  }
  return (
    <div role="tablist" aria-label={etiqueta} className={`flex flex-wrap gap-x-8 border-b border-white/16 ${className}`}>
      {pestanas.map((p, i) => {
        const activa = p.valor === valor
        return (
          <button
            key={p.valor}
            ref={(el) => (refs.current[p.valor] = el)}
            type="button"
            role="tab"
            id={`${idPanel}-tab-${p.valor}`}
            aria-selected={activa}
            aria-controls={idPanel}
            tabIndex={activa ? 0 : -1}
            onClick={() => onCambiar(p.valor)}
            onKeyDown={(e) => mover(e, i)}
            className={`-mb-px inline-flex min-h-12 items-center border-b-2 px-1 text-[15px] transition-colors ${
              activa ? 'border-coral font-bold text-white' : 'border-transparent font-medium text-lavanda hover:text-white'
            }`}
          >
            {p.texto}
          </button>
        )
      })}
    </div>
  )
}
