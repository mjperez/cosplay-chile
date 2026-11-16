import { useState } from 'react'
import { api } from '../../api/client'
import { useMeta } from '../../contexto/MetaContext'
import { InsigniaNivel } from '../../components/diseno/Insignias'
import useApi from '../../components/useApi'
import { Alerta, AreaTexto, Cargando, Vacio, haceTiempo } from '../../components/ui'
import TarjetaModeracion from './TarjetaModeracion'

// Revisión editorial de tutoriales enviados (UC6: el moderador publica o rechaza)
export default function ColaContenidos() {
  const { etiqueta } = useMeta()
  const { datos, error, cargando, recargar } = useApi('/api/moderacion/contenidos')
  const [motivos, setMotivos] = useState({})
  const [aviso, setAviso] = useState(null)

  const decidir = async (c, aprobar) => {
    setAviso(null)
    try {
      if (aprobar) await api(`/api/moderacion/contenidos/${c.id}/publicar`, { method: 'POST' })
      else await api(`/api/moderacion/contenidos/${c.id}/rechazar`, { method: 'POST', body: { motivo: motivos[c.id] || '' } })
      setAviso({ tipo: 'exito', texto: aprobar ? `Publicaste «${c.titulo}». Se notificó a la comunidad.` : `Rechazaste «${c.titulo}». Se notificó al autor.` })
      recargar()
    } catch (e) {
      setAviso({ tipo: 'error', texto: e.campos?.motivo ? `Motivo: ${e.campos.motivo}` : e.message })
    }
  }

  const resumen = (c) =>
    [
      c.pasos && `${c.pasos.length} pasos · ${c.materiales?.length || 0} materiales`,
      c.preguntas && `${c.preguntas.length} preguntas a ${c.entrevistado}`,
      c.enlaces && `${c.enlaces.length} enlaces de referencia`,
      c.imagen_url ? 'Con imagen' : 'Sin imágenes adjuntas',
      c.video_url && 'Con video',
    ].filter(Boolean).join(' · ')

  return (
    <div>
      <Alerta tipo={aviso?.tipo} className="mb-4">{aviso?.texto}</Alerta>
      {cargando && <Cargando />}
      <Alerta tipo="error">{error?.message}</Alerta>
      {datos && <p className="mb-4 text-sm text-lavanda" role="status">{datos.length === 1 ? '1 por revisar' : `${datos.length} por revisar`}</p>}
      {datos?.length === 0 && <Vacio>No quedan tutoriales por revisar.</Vacio>}
      <ul className="space-y-4">
        {datos?.map((c) => (
          <TarjetaModeracion
            key={c.id}
            titulo={c.titulo}
            meta={`${etiqueta('tipos_contenido', c.tipo)} · enviado ${haceTiempo(c.created_at)}`}
            autor={c.autor?.nombre}
            enlace={`/guias/${c.id}`}
            etiquetas={<><InsigniaNivel nivel={c.nivel} /><span className="etiqueta">{c.categoria.nombre}</span></>}
          >
            <p className="mt-3 text-sm text-tinta">{c.descripcion}</p>
            <p className="mt-1 text-[13px] text-lavanda">{resumen(c)}</p>
            <AreaTexto
              etiqueta="Comentario de rechazo (obligatorio solo si rechazas)"
              rows={2}
              className="mt-4"
              value={motivos[c.id] || ''}
              onChange={(e) => setMotivos((m) => ({ ...m, [c.id]: e.target.value }))}
            />
            <div className="mt-4 flex flex-wrap gap-3">
              <button className="boton-marca" onClick={() => decidir(c, true)}>Aprobar y publicar<span className="sr-only">: {c.titulo}</span></button>
              <button className="boton-contorno" onClick={() => decidir(c, false)}>Rechazar con comentario<span className="sr-only">: {c.titulo}</span></button>
            </div>
          </TarjetaModeracion>
        ))}
      </ul>
    </div>
  )
}
