import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Icono from './diseno/Icono'

// Notificaciones internas (RF-37) generadas por el NotificacionInternaObserver
export default function CampanaNotificaciones() {
  const [abierta, setAbierta] = useState(false)
  const [bandeja, setBandeja] = useState({ no_leidas: 0, items: [] })
  const contenedor = useRef(null)
  const boton = useRef(null)
  const navigate = useNavigate()
  const location = useLocation()

  const cargar = useCallback(async () => {
    try {
      setBandeja(await api('/api/notificaciones?limite=15'))
    } catch {
      /* sin conexión: se reintenta en el próximo ciclo */
    }
  }, [])

  useEffect(() => {
    cargar()
    const t = setInterval(cargar, 60000)
    return () => clearInterval(t)
  }, [cargar, location.pathname])

  useEffect(() => {
    if (!abierta) return
    const alClick = (e) => !contenedor.current?.contains(e.target) && setAbierta(false)
    const alTecla = (e) => {
      if (e.key === 'Escape') {
        setAbierta(false)
        boton.current?.focus()
      }
    }
    document.addEventListener('mousedown', alClick)
    document.addEventListener('keydown', alTecla)
    return () => {
      document.removeEventListener('mousedown', alClick)
      document.removeEventListener('keydown', alTecla)
    }
  }, [abierta])

  const abrir = async (n) => {
    setAbierta(false)
    if (!n.leida) {
      await api(`/api/notificaciones/${n.id}/leer`, { method: 'POST' }).catch(() => {})
      cargar()
    }
    if (n.enlace) navigate(n.enlace)
  }

  const leerTodas = async () => {
    await api('/api/notificaciones/leer-todas', { method: 'POST' }).catch(() => {})
    cargar()
  }

  return (
    <div className="relative" ref={contenedor}>
      <button
        ref={boton}
        className="relative inline-flex size-11 items-center justify-center rounded-full text-white hover:text-durazno"
        aria-expanded={abierta}
        aria-controls="panel-notificaciones"
        onClick={() => setAbierta((v) => !v)}
      >
        <Icono nombre="campana" tamano={22} />
        <span className="sr-only">Notificaciones{bandeja.no_leidas ? `, ${bandeja.no_leidas} sin leer` : ''}</span>
        {bandeja.no_leidas > 0 && (
          <span aria-hidden="true" className="absolute right-0.5 top-0.5 min-w-5 rounded-full bg-fucsia px-1 text-center text-xs font-bold text-tinta-oscura">
            {bandeja.no_leidas > 9 ? '9+' : bandeja.no_leidas}
          </span>
        )}
      </button>
      {abierta && (
        <div
          id="panel-notificaciones"
          className="absolute right-0 z-[600] mt-2 w-[min(22rem,90vw)] rounded-[18px] border border-white/16 bg-panel p-3 shadow-2xl"
          role="region"
          aria-label="Notificaciones"
        >
          <div className="flex items-center justify-between gap-2 px-1 pb-2">
            <h2 className="font-display text-lg font-bold">Notificaciones</h2>
            {bandeja.no_leidas > 0 && (
              <button className="enlace-claro min-h-11 text-sm" onClick={leerTodas}>Marcar todas como leídas</button>
            )}
          </div>
          {bandeja.items.length === 0 ? (
            <p className="px-1 py-4 text-sm text-lavanda">No tienes notificaciones.</p>
          ) : (
            <ul className="max-h-96 overflow-y-auto">
              {bandeja.items.map((n) => (
                <li key={n.id} className="border-t border-white/12">
                  <button
                    className={`flex w-full gap-2.5 rounded-lg px-1 py-2.5 text-left text-sm hover:bg-white/6 ${n.leida ? 'text-lavanda' : 'font-bold text-white'}`}
                    onClick={() => abrir(n)}
                  >
                    <span aria-hidden="true" className={`mt-1.5 size-2 shrink-0 rounded-full ${n.leida ? 'bg-transparent' : 'bg-fucsia'}`} />
                    <span>
                      {!n.leida && <span className="sr-only">Sin leer: </span>}
                      {n.mensaje}
                      <span className="block text-xs font-normal text-lavanda">
                        {new Date(n.created_at).toLocaleString('es-CL', { dateStyle: 'medium', timeStyle: 'short' })}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
