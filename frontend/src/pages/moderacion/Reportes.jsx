import { useState } from 'react'
import { api } from '../../api/client'
import { useMeta } from '../../contexto/MetaContext'
import useApi from '../../components/useApi'
import { Alerta, AreaTexto, Cargando, GrupoChips, Selector, Vacio, formatoFecha } from '../../components/ui'
import TarjetaModeracion from './TarjetaModeracion'

const TIPOS = {
  CONTENIDO: 'Guía o artículo', TEMA: 'Tema del foro', RESPUESTA: 'Respuesta del foro', EVENTO: 'Evento',
  DIRECTORIO: 'Ficha del directorio', RESENA: 'Reseña', PARTICIPACION_DESAFIO: 'Participación en desafío',
}
const ACCIONES = [
  { valor: 'DESCARTAR', texto: 'Descartar reporte (no infringe las normas)' },
  { valor: 'RESOLVER', texto: 'Marcar resuelto (sin sanción; p. ej. evento corregido)' },
  { valor: 'OCULTAR', texto: 'Ocultar el contenido' },
  { valor: 'OCULTAR_Y_SUSPENDER', texto: 'Ocultar y suspender a quien lo publicó' },
]

// Gestionar Soporte y Reportes (Fig. 10) con extensión Bloquear/Sancionar Usuario
export default function Reportes() {
  const { etiqueta } = useMeta()
  const [estado, setEstado] = useState('ABIERTO')
  const { datos, error, cargando, recargar } = useApi(`/api/moderacion/reportes?estado=${estado}`)
  const [form, setForm] = useState({})
  const [aviso, setAviso] = useState(null)

  const resolver = async (r) => {
    const f = form[r.id] || {}
    try {
      await api(`/api/moderacion/reportes/${r.id}/resolver`, {
        method: 'POST', body: { accion: f.accion || 'DESCARTAR', resolucion: f.resolucion || '' },
      })
      setAviso({ tipo: 'exito', texto: 'Reporte resuelto y registrado en la bitácora.' })
      recargar()
    } catch (e) {
      setAviso({ tipo: 'error', texto: e.campos?.resolucion ? `Resolución: ${e.campos.resolucion}` : e.message })
    }
  }
  const set = (id, campo, valor) => setForm((x) => ({ ...x, [id]: { ...x[id], [campo]: valor } }))

  return (
    <div>
      <GrupoChips
        etiqueta="Mostrar"
        className="mb-5"
        valor={estado}
        onCambiar={setEstado}
        opciones={[{ valor: 'ABIERTO', texto: 'Abiertos' }, { valor: 'RESUELTO', texto: 'Resueltos' }, { valor: 'DESCARTADO', texto: 'Descartados' }]}
      />
      <Alerta tipo={aviso?.tipo} className="mb-4">{aviso?.texto}</Alerta>
      {cargando && <Cargando />}
      <Alerta tipo="error">{error?.message}</Alerta>
      {datos?.length === 0 && <Vacio>No quedan reportes en este estado.</Vacio>}
      <ul className="space-y-4">
        {datos?.map((r) => (
          <TarjetaModeracion
            key={r.id}
            titulo={TIPOS[r.tipo_objeto]}
            meta={`Motivo: ${etiqueta('motivos_reporte', r.motivo)}`}
            autor={`Reporta: ${r.reportante?.nombre || 'cuenta eliminada'} · ${formatoFecha(r.created_at)}`}
            enlace={r.objeto_enlace}
            textoEnlace="Ver en contexto"
            etiquetas={
              <>
                {r.objeto_oculto && <span className="insignia bg-estrella text-[#2a1c00]">Oculto</span>}
                {r.autor_objeto_estado === 'SUSPENDIDO' && <span className="insignia bg-peligro text-[#2a0606]">Autor suspendido</span>}
              </>
            }
          >
            <blockquote className="mt-3 border-l-2 border-coral pl-4 text-sm text-tinta">{r.objeto_texto}</blockquote>
            <p className="mt-2 text-[13px] text-lavanda">Publicado por: {r.autor_objeto?.nombre || '—'}</p>
            {r.detalle && <p className="mt-1 text-sm text-tinta"><strong className="text-white">Detalle del reporte:</strong> {r.detalle}</p>}
            {r.estado === 'ABIERTO' ? (
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <Selector etiqueta="Acción" opciones={ACCIONES} value={form[r.id]?.accion || 'DESCARTAR'} onChange={(e) => set(r.id, 'accion', e.target.value)} />
                <AreaTexto etiqueta="Resolución (queda en la bitácora)" rows={2} value={form[r.id]?.resolucion || ''} onChange={(e) => set(r.id, 'resolucion', e.target.value)} />
                <button className="boton-marca sm:col-span-2 sm:w-fit" onClick={() => resolver(r)}>
                  Aplicar<span className="sr-only"> al reporte sobre {TIPOS[r.tipo_objeto]}</span>
                </button>
              </div>
            ) : (
              <p className="mt-3 text-sm text-tinta"><strong className="text-white">Resolución:</strong> {r.resolucion}</p>
            )}
          </TarjetaModeracion>
        ))}
      </ul>
    </div>
  )
}
