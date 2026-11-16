import { useEffect, useId, useRef, useState } from 'react'
import Icono from './diseno/Icono'

// RF-05: compartir en redes sociales sin servicios de terceros incrustados (solo enlaces de intención).
export default function CompartirRedes({ titulo, ruta, variante = 'icono' }) {
  const id = useId()
  const [abierto, setAbierto] = useState(false)
  const [aviso, setAviso] = useState('')
  const caja = useRef(null)
  const boton = useRef(null)
  const url = new URL(ruta || window.location.pathname, window.location.origin).toString()
  const texto = `${titulo} · Cosplay Chile`

  useEffect(() => {
    if (!abierto) return
    const fuera = (e) => !caja.current?.contains(e.target) && setAbierto(false)
    const tecla = (e) => {
      if (e.key === 'Escape') {
        setAbierto(false)
        boton.current?.focus()
      }
    }
    document.addEventListener('mousedown', fuera)
    document.addEventListener('keydown', tecla)
    return () => {
      document.removeEventListener('mousedown', fuera)
      document.removeEventListener('keydown', tecla)
    }
  }, [abierto])

  const redes = [
    { nombre: 'WhatsApp', href: `https://wa.me/?text=${encodeURIComponent(`${texto} ${url}`)}` },
    { nombre: 'X (Twitter)', href: `https://twitter.com/intent/tweet?text=${encodeURIComponent(texto)}&url=${encodeURIComponent(url)}` },
    { nombre: 'Facebook', href: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}` },
  ]

  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setAviso('Enlace copiado')
    } catch {
      setAviso(`Copia este enlace: ${url}`)
    }
  }
  const nativo = async () => {
    try {
      await navigator.share({ title: texto, url })
      setAbierto(false)
    } catch {
      /* la persona canceló */
    }
  }

  return (
    <span className="relative inline-flex" ref={caja}>
      <button
        ref={boton}
        type="button"
        className={variante === 'icono' ? 'boton-icono' : 'boton-contorno'}
        aria-expanded={abierto}
        aria-controls={`${id}-menu`}
        aria-label={variante === 'icono' ? `Compartir en redes sociales: ${titulo}` : undefined}
        onClick={() => {
          setAviso('')
          setAbierto((v) => !v)
        }}
      >
        <Icono nombre="compartir" tamano={variante === 'icono' ? 18 : 16} />
        {variante !== 'icono' && 'Compartir'}
      </button>
      {abierto && (
        <div id={`${id}-menu`} className="absolute right-0 top-full z-[650] mt-2 w-60 rounded-[18px] border border-white/16 bg-panel p-2 shadow-2xl">
          <p className="px-3 pb-1 pt-2 text-xs font-bold uppercase tracking-[.16em] text-durazno">Compartir en</p>
          <ul>
            {redes.map((r) => (
              <li key={r.nombre}>
                <a
                  href={r.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm text-white no-underline hover:bg-white/8"
                >
                  {r.nombre} <span className="sr-only">(se abre en otra pestaña)</span>
                  <Icono nombre="externo" tamano={14} className="ml-auto text-durazno" />
                </a>
              </li>
            ))}
            <li>
              <button type="button" onClick={copiar} className="flex min-h-11 w-full items-center gap-3 rounded-lg px-3 text-left text-sm text-white hover:bg-white/8">
                <Icono nombre="enlace" tamano={16} className="text-durazno" /> Copiar enlace
              </button>
            </li>
            {typeof navigator !== 'undefined' && navigator.share && (
              <li>
                <button type="button" onClick={nativo} className="flex min-h-11 w-full items-center gap-3 rounded-lg px-3 text-left text-sm text-white hover:bg-white/8">
                  <Icono nombre="compartir" tamano={16} className="text-durazno" /> Más opciones…
                </button>
              </li>
            )}
          </ul>
          <p role="status" className="break-all px-3 text-xs text-exito">{aviso}</p>
        </div>
      )}
    </span>
  )
}
