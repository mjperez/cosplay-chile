import { useEffect, useId, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Icono from './diseno/Icono'

const ETIQUETA_TIPO = {
  guia: 'Guía', proveedor: 'Profesional', tienda: 'Tienda', comunidad: 'Comunidad', tema: 'Foro', evento: 'Evento',
}

// RF-31: buscador unificado con autocompletado (patrón ARIA combobox).
// variante «barra»: encabezado de las páginas internas · «portada»: buscador grande de la portada
export default function BuscadorGlobal({ variante = 'barra' }) {
  const id = useId()
  const navigate = useNavigate()
  const location = useLocation()
  const [q, setQ] = useState('')
  const [sugerencias, setSugerencias] = useState([])
  const [abierto, setAbierto] = useState(false)
  const [activa, setActiva] = useState(-1)
  const contenedor = useRef(null)
  const portada = variante === 'portada'

  useEffect(() => {
    setAbierto(false)
    setQ('')
  }, [location.pathname])

  useEffect(() => {
    if (q.trim().length < 2) {
      setSugerencias([])
      return
    }
    const control = new AbortController()
    const t = setTimeout(() => {
      api(`/api/busqueda/sugerencias?q=${encodeURIComponent(q.trim())}`, { signal: control.signal })
        .then((s) => {
          setSugerencias(s)
          setActiva(-1)
          setAbierto(true)
        })
        .catch(() => {})
    }, 250)
    return () => {
      clearTimeout(t)
      control.abort()
    }
  }, [q])

  useEffect(() => {
    const fuera = (e) => !contenedor.current?.contains(e.target) && setAbierto(false)
    document.addEventListener('mousedown', fuera)
    return () => document.removeEventListener('mousedown', fuera)
  }, [])

  const irA = (s) => {
    setAbierto(false)
    navigate(s.enlace)
  }

  const enviar = (e) => {
    e.preventDefault()
    if (activa >= 0 && sugerencias[activa]) return irA(sugerencias[activa])
    if (q.trim().length >= 2) {
      setAbierto(false)
      navigate(`/buscar?q=${encodeURIComponent(q.trim())}`)
    }
  }

  const alTeclado = (e) => {
    if (e.key === 'ArrowDown' && sugerencias.length) {
      e.preventDefault()
      setAbierto(true)
      setActiva((a) => (a + 1) % sugerencias.length)
    } else if (e.key === 'ArrowUp' && sugerencias.length) {
      e.preventDefault()
      setActiva((a) => (a <= 0 ? sugerencias.length - 1 : a - 1))
    } else if (e.key === 'Escape') {
      setAbierto(false)
      setActiva(-1)
    }
  }

  const lista = `${id}-lista`
  const mostrar = abierto && q.trim().length >= 2
  return (
    <form role="search" onSubmit={enviar} className={`relative w-full ${portada ? 'max-w-[520px]' : 'max-w-[320px]'}`} ref={contenedor}>
      <label htmlFor={`${id}-q`} className="sr-only">
        {portada ? 'Buscar guías, profesionales, tiendas y eventos' : 'Búsqueda global'}
      </label>
      <div
        className={`flex items-center gap-2.5 rounded-full border bg-noche/80 focus-within:border-coral has-[input:focus-visible]:outline-2 has-[input:focus-visible]:outline-offset-3 has-[input:focus-visible]:outline-cian ${
          portada ? 'min-h-14 border-white/60 pl-[18px] pr-2' : 'min-h-11 border-white/30 pl-4 pr-1.5'
        }`}
      >
        <Icono nombre="buscar" tamano={portada ? 20 : 17} className="text-lavanda" />
        <input
          id={`${id}-q`}
          type="search"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={mostrar}
          aria-controls={lista}
          aria-activedescendant={activa >= 0 ? `${id}-op-${activa}` : undefined}
          autoComplete="off"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={alTeclado}
          onFocus={() => sugerencias.length && setAbierto(true)}
          placeholder={portada ? 'Prueba “EVA”, “maquillaje” o “Santiago”' : 'Buscar en todo el sitio'}
          className={`min-w-0 flex-1 bg-transparent text-white outline-none focus-visible:outline-none ${portada ? 'text-base' : 'text-sm'}`}
        />
        {portada ? (
          <button className="inline-flex min-h-11 items-center rounded-full bg-linear-120 from-coral to-fucsia px-[22px] text-xs font-bold uppercase tracking-[.14em] text-tinta-oscura hover:brightness-110">
            Buscar
          </button>
        ) : (
          <button className="sr-only">Buscar</button>
        )}
      </div>
      <p className="sr-only" role="status" aria-live="polite">
        {mostrar ? `${sugerencias.length} sugerencias disponibles. Usa las flechas para recorrerlas.` : ''}
      </p>
      {mostrar && (
        <ul
          id={lista}
          role="listbox"
          aria-label="Sugerencias"
          className="absolute left-0 right-0 z-[700] mt-2 max-h-96 overflow-y-auto rounded-[18px] border border-white/16 bg-noche/95 px-[18px] py-1.5 shadow-2xl backdrop-blur"
        >
          {sugerencias.length === 0 && <li className="py-3 text-sm text-lavanda">Sin sugerencias. Presiona Enter para buscar.</li>}
          {sugerencias.map((s, i) => (
            <li
              key={`${s.tipo}-${s.id}`}
              id={`${id}-op-${i}`}
              role="option"
              aria-selected={i === activa}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => irA(s)}
              className={`flex min-h-11 cursor-pointer items-center gap-3 border-b border-white/14 py-2 text-sm text-white last:border-b-0 ${
                i === activa ? 'text-durazno' : 'hover:text-durazno'
              }`}
            >
              <span className="w-[84px] shrink-0 text-xs uppercase tracking-[.12em] text-durazno">{ETIQUETA_TIPO[s.tipo]}</span>
              <span className="min-w-0">
                <span className="block truncate">{s.titulo}</span>
                {s.subtitulo && <span className="block truncate text-xs text-lavanda">{s.subtitulo}</span>}
              </span>
            </li>
          ))}
        </ul>
      )}
    </form>
  )
}
