import { useState } from 'react'
import { api } from '../../api/client'
import { useMeta } from '../../contexto/MetaContext'
import { InsigniaEvento } from '../../components/diseno/Insignias'
import useApi from '../../components/useApi'
import { Alerta, Cargando, Vacio, formatoFecha } from '../../components/ui'
import TarjetaModeracion from './TarjetaModeracion'

// RF-17: eventos sugeridos por la comunidad
export default function EventosPendientes() {
  const { etiqueta } = useMeta()
  const { datos, error, cargando, recargar } = useApi('/api/moderacion/eventos')
  const [aviso, setAviso] = useState(null)

  const decidir = async (e, decision) => {
    try {
      await api(`/api/moderacion/eventos/${e.id}/${decision}`, { method: 'POST' })
      setAviso({ tipo: 'exito', texto: decision === 'aprobar' ? `«${e.nombre}» ya está en el calendario.` : `Descartaste «${e.nombre}».` })
      recargar()
    } catch (err) {
      setAviso({ tipo: 'error', texto: err.message })
    }
  }

  return (
    <div>
      <p className="mb-4 text-sm text-lavanda">
        Los cambios en eventos ya publicados llegan como reportes con el motivo «actualización de evento», en «Reportes de contenido».
      </p>
      <Alerta tipo={aviso?.tipo} className="mb-4">{aviso?.texto}</Alerta>
      {cargando && <Cargando />}
      <Alerta tipo="error">{error?.message}</Alerta>
      {datos?.length === 0 && <Vacio>No quedan eventos sugeridos por revisar.</Vacio>}
      <ul className="space-y-4">
        {datos?.map((e) => (
          <TarjetaModeracion
            key={e.id}
            titulo={e.nombre}
            meta={`${formatoFecha(e.fecha_inicio)} · ${e.comuna || e.lugar}, ${etiqueta('regiones', e.region)}`}
            autor={`Sugerido por ${e.sugerido_por?.nombre || 'la comunidad'}`}
            enlace={`/calendario/${e.id}`}
            etiquetas={<InsigniaEvento tipo={e.tipo} />}
          >
            <p className="mt-2 text-sm text-tinta">{e.lugar}</p>
            {e.enlace_oficial && (
              <p className="mt-1 text-[13px]">
                Enlace oficial: <a href={e.enlace_oficial} className="enlace-claro break-all" target="_blank" rel="noreferrer">{e.enlace_oficial}</a>
              </p>
            )}
            <div className="mt-4 flex flex-wrap gap-3">
              <button className="boton-marca" onClick={() => decidir(e, 'aprobar')}>Publicar en calendario<span className="sr-only">: {e.nombre}</span></button>
              <button className="boton-contorno" onClick={() => decidir(e, 'rechazar')}>Descartar<span className="sr-only">: {e.nombre}</span></button>
            </div>
          </TarjetaModeracion>
        ))}
      </ul>
    </div>
  )
}
