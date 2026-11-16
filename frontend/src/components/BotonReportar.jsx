import { useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../contexto/AuthContext'
import { useMeta } from '../contexto/MetaContext'
import Icono from './diseno/Icono'
import { Alerta, AreaTexto, Selector } from './ui'

// RF-38 (contenido inapropiado) y RF-17 (reportar actualizaciones de un evento)
// variante «enlace»: texto con bandera · «chip»: botón redondeado pequeño (listas del foro)
export default function BotonReportar({ tipo, objetoId, texto, compacto = false, variante = 'enlace', nombre = '' }) {
  const { usuario } = useAuth()
  const { opciones } = useMeta()
  const location = useLocation()
  const dialogo = useRef(null)
  const esEvento = tipo === 'EVENTO'
  const [motivo, setMotivo] = useState(esEvento ? 'ACTUALIZACION_EVENTO' : 'INAPROPIADO')
  const [detalle, setDetalle] = useState('')
  const [resultado, setResultado] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const etiquetaBoton = texto || (esEvento ? 'Reportar un cambio' : 'Reportar')
  const clase =
    variante === 'chip'
      ? 'inline-flex min-h-11 items-center gap-2 rounded-full border border-white/30 px-3.5 text-[13px] text-white hover:border-coral sm:min-h-9'
      : `inline-flex min-h-11 items-center gap-2 text-[13px] text-[var(--texto-suave)] underline decoration-1 underline-offset-[3px] hover:text-[var(--enlace)] ${compacto ? 'sm:min-h-0' : ''}`

  if (!usuario) {
    if (compacto) return null
    return (
      <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname)}`} className={clase}>
        <Icono nombre="bandera" tamano={15} /> Inicia sesión para reportar
      </Link>
    )
  }

  const motivos = opciones('motivos_reporte').filter((o) => esEvento || o.valor !== 'ACTUALIZACION_EVENTO')
  const abrir = () => {
    setResultado(null)
    dialogo.current?.showModal()
  }
  const cerrar = () => dialogo.current?.close()

  const enviar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    try {
      const r = await api('/api/reportes', { method: 'POST', body: { tipo_objeto: tipo, objeto_id: objetoId, motivo, detalle } })
      setResultado({ tipo: 'exito', texto: r.mensaje })
      setDetalle('')
    } catch (err) {
      setResultado({ tipo: 'error', texto: err.message })
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      <button type="button" className={clase} onClick={abrir} aria-label={nombre ? `${etiquetaBoton}: ${nombre}` : undefined}>
        <Icono nombre="bandera" tamano={15} /> {etiquetaBoton}
      </button>
      <dialog
        ref={dialogo}
        aria-labelledby={`titulo-reporte-${objetoId}`}
        className="m-auto w-[min(32rem,92vw)] rounded-[18px] border border-white/16 bg-panel p-0 text-tinta backdrop:bg-noche/70"
      >
        <form onSubmit={enviar} className="space-y-4 p-6">
          <h2 id={`titulo-reporte-${objetoId}`} className="font-display text-2xl font-bold text-white">
            {esEvento ? 'Reportar un cambio en el evento' : 'Reportar contenido'}
          </h2>
          <p className="text-sm text-lavanda">
            {esEvento
              ? 'Cuéntanos qué cambió (fecha, lugar, enlace) o qué problema encontraste.'
              : 'Tu reporte es confidencial. El equipo de moderación lo revisa de forma manual.'}
          </p>
          <Alerta tipo={resultado?.tipo}>{resultado?.texto}</Alerta>
          {resultado?.tipo !== 'exito' && (
            <>
              <Selector etiqueta="Motivo" opciones={motivos} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
              <AreaTexto etiqueta="Detalle (opcional)" rows={3} maxLength={2000} value={detalle} onChange={(e) => setDetalle(e.target.value)} />
            </>
          )}
          <div className="flex flex-wrap justify-end gap-2">
            <button type="button" className="boton-contorno" onClick={cerrar}>{resultado?.tipo === 'exito' ? 'Cerrar' : 'Cancelar'}</button>
            {resultado?.tipo !== 'exito' && <button className="boton-marca" disabled={enviando}>Enviar reporte</button>}
          </div>
        </form>
      </dialog>
    </>
  )
}
