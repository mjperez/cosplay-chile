import { useState } from 'react'
import { api } from '../../api/client'
import useApi from '../../components/useApi'
import { Alerta, AreaTexto, Campo, Selector } from '../../components/ui'
import { nombreMes } from '../desafios/Desafios'

// RF-36: lanzar desafíos mensuales y elegir ganador
export default function DesafiosAdmin() {
  const hoy = new Date()
  const [f, setF] = useState({ titulo: '', descripcion: '', mes: String(((hoy.getMonth() + 1) % 12) + 1), anio: String(hoy.getMonth() === 11 ? hoy.getFullYear() + 1 : hoy.getFullYear()) })
  const [aviso, setAviso] = useState(null)
  const { datos: desafios, recargar } = useApi('/api/desafios')
  const [elegido, setElegido] = useState('')
  const seleccionado = desafios?.find((d) => d.id === elegido)
  const detalle = useApi(elegido ? `/api/desafios/${elegido}` : null)
  const [ganador, setGanador] = useState('')

  const crear = async (e) => {
    e.preventDefault()
    try {
      await api('/api/moderacion/desafios', { method: 'POST', body: { ...f, mes: Number(f.mes), anio: Number(f.anio) } })
      setAviso({ tipo: 'exito', texto: 'Desafío publicado. Se notificó a toda la comunidad.' })
      setF((x) => ({ ...x, titulo: '', descripcion: '' }))
      recargar()
    } catch (err) {
      setAviso({ tipo: 'error', texto: err.message })
    }
  }
  const elegir = async () => {
    try {
      await api(`/api/moderacion/desafios/${elegido}/ganador`, { method: 'POST', body: { participacion_id: ganador } })
      setAviso({ tipo: 'exito', texto: 'Ganador registrado y notificado.' })
      recargar()
      detalle.recargar()
    } catch (err) {
      setAviso({ tipo: 'error', texto: err.message })
    }
  }
  const meses = Array.from({ length: 12 }, (_, i) => ({ valor: String(i + 1), texto: new Date(2026, i, 1).toLocaleDateString('es-CL', { month: 'long' }) }))

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Alerta tipo={aviso?.tipo} className="lg:col-span-2">{aviso?.texto}</Alerta>
      <form onSubmit={crear} className="panel space-y-4 p-6" aria-labelledby="t-nuevo-desafio">
        <h2 id="t-nuevo-desafio" className="font-display text-2xl font-bold text-white">Lanzar un desafío</h2>
        <Campo etiqueta="Título" requerido value={f.titulo} onChange={(e) => setF({ ...f, titulo: e.target.value })} />
        <AreaTexto etiqueta="Descripción y reglas" requerido rows={3} value={f.descripcion} onChange={(e) => setF({ ...f, descripcion: e.target.value })} />
        <div className="grid grid-cols-2 gap-3">
          <Selector etiqueta="Mes" opciones={meses} value={f.mes} onChange={(e) => setF({ ...f, mes: e.target.value })} />
          <Campo etiqueta="Año" type="number" value={f.anio} onChange={(e) => setF({ ...f, anio: e.target.value })} />
        </div>
        <button className="boton-marca">Publicar desafío</button>
      </form>
      <section className="panel space-y-4 p-6" aria-labelledby="t-ganador">
        <h2 id="t-ganador" className="font-display text-2xl font-bold text-white">Elegir ganador</h2>
        <Selector etiqueta="Desafío" vacio="Elige un desafío" value={elegido} onChange={(e) => { setElegido(e.target.value); setGanador('') }}
          opciones={(desafios || []).map((d) => ({ valor: d.id, texto: `${nombreMes(d.mes, d.anio)}: ${d.titulo}${d.ganador ? ' (con ganador)' : ''}` }))} />
        {seleccionado && detalle.datos && (
          detalle.datos.lista_participaciones.length === 0 ? <p className="text-sm text-lavanda">Sin participaciones.</p> : (
            <>
              <Selector etiqueta="Participación ganadora" vacio="Elige una participación" value={ganador} onChange={(e) => setGanador(e.target.value)}
                opciones={detalle.datos.lista_participaciones.map((p) => ({ valor: p.id, texto: `${p.titulo} — ${p.autor?.nombre}` }))} />
              <button className="boton-marca" disabled={!ganador} onClick={elegir}>Registrar ganador</button>
            </>
          )
        )}
      </section>
    </div>
  )
}
