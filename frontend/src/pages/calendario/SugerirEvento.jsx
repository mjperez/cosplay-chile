import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { useMeta } from '../../contexto/MetaContext'
import { Alerta, AreaTexto, Campo, EncabezadoPagina, Selector, useTitulo } from '../../components/ui'

const VACIO = { nombre: '', tipo: 'MEETUP', fecha_inicio: '', fecha_fin: '', lugar: '', comuna: '', region: 'RM', enlace_oficial: '', descripcion: '' }

// RF-17: los usuarios sugieren eventos; moderación los revisa antes de publicarlos
export function FormSugerirEvento() {
  const { opciones } = useMeta()
  const [f, setF] = useState(VACIO)
  const [error, setError] = useState(null)
  const [listo, setListo] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const set = (c) => (e) => setF((x) => ({ ...x, [c]: e.target.value }))
  const err = (c) => error?.campos?.[c]

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      const r = await api('/api/eventos/sugerir', {
        method: 'POST',
        body: { ...f, fecha_fin: f.fecha_fin || null, enlace_oficial: f.enlace_oficial || null, comuna: f.comuna || null },
      })
      setListo(r)
      setF(VACIO)
    } catch (e2) {
      setError(e2)
    } finally {
      setEnviando(false)
    }
  }

  if (listo) {
    return (
      <div>
        <Alerta tipo="exito">
          <strong>¡Gracias por tu sugerencia!</strong> «{listo.nombre}» quedó pendiente de revisión. Te avisaremos cuando aparezca en el calendario.
        </Alerta>
        <button type="button" className="boton-contorno mt-4" onClick={() => setListo(null)}>Sugerir otro evento</button>
      </div>
    )
  }

  const hoy = new Date().toISOString().slice(0, 10)
  return (
    <form onSubmit={enviar} className="space-y-5" noValidate aria-label="Sugerir un evento">
      <Alerta tipo="error">{error?.message}</Alerta>
      <div className="grid gap-5 sm:grid-cols-2">
        <Campo etiqueta="Nombre del evento" requerido value={f.nombre} onChange={set('nombre')} error={err('nombre')} placeholder="Ej.: Convención de primavera" />
        <Selector etiqueta="Tipo" opciones={opciones('tipos_evento')} value={f.tipo} onChange={set('tipo')} />
        <Campo etiqueta="Fecha" type="date" min={hoy} requerido value={f.fecha_inicio} onChange={set('fecha_inicio')} error={err('fecha_inicio')} />
        <Campo etiqueta="Fecha de término" type="date" min={f.fecha_inicio || hoy} value={f.fecha_fin} onChange={set('fecha_fin')} error={err('fecha_fin')} ayuda="Opcional, si dura más de un día" />
        <Campo etiqueta="Ciudad o comuna" value={f.comuna} onChange={set('comuna')} error={err('comuna')} placeholder="Ej.: Temuco" />
        <Selector etiqueta="Región" requerido opciones={opciones('regiones')} value={f.region} onChange={set('region')} />
        <Campo etiqueta="Lugar o recinto" requerido value={f.lugar} onChange={set('lugar')} error={err('lugar')} placeholder="Nombre del recinto" />
        <Campo etiqueta="Enlace oficial o de entradas" type="url" value={f.enlace_oficial} onChange={set('enlace_oficial')} error={err('enlace_oficial')} placeholder="https://" />
      </div>
      <AreaTexto etiqueta="Descripción (opcional)" rows={3} value={f.descripcion} onChange={set('descripcion')} error={err('descripcion')} />
      <p className="text-[13px] text-lavanda">
        ¿Es un cambio en un evento que ya está en el calendario? Usa «Reportar un cambio» en ese evento.
      </p>
      <button className="boton-marca boton-grande" disabled={enviando}>{enviando ? 'Enviando…' : 'Enviar sugerencia'}</button>
    </form>
  )
}

export default function SugerirEvento() {
  useTitulo('Sugerir un evento')
  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { a: '/calendario', texto: 'Calendario' }, { texto: 'Sugerir un evento' }]}
        titulo="Sugiere un evento"
        bajada="¿Conoces una convención, concurso, meetup o taller que no está en el calendario? Cuéntanos y el equipo lo revisa antes de publicarlo."
      />
      <div className="contenedor mt-10 max-w-4xl">
        <div className="panel p-6 sm:p-8">
          <FormSugerirEvento />
        </div>
        <Link to="/calendario" className="boton-contorno mt-6">Volver al calendario</Link>
      </div>
    </div>
  )
}
