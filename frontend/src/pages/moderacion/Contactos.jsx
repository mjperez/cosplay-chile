import { useState } from 'react'
import { api } from '../../api/client'
import { useMeta } from '../../contexto/MetaContext'
import useApi from '../../components/useApi'
import { Alerta, Cargando, GrupoChips, Vacio, formatoFecha } from '../../components/ui'
import TarjetaModeracion from './TarjetaModeracion'

// RF-40: mensajes del formulario de contacto
export default function Contactos() {
  const { etiqueta } = useMeta()
  const [estado, setEstado] = useState('NUEVO')
  const { datos, error, cargando, recargar } = useApi(`/api/moderacion/contactos?estado=${estado}`)
  const [aviso, setAviso] = useState('')
  const atender = async (c) => {
    try {
      await api(`/api/moderacion/contactos/${c.id}/atender`, { method: 'POST' })
      recargar()
    } catch (e) {
      setAviso(e.message)
    }
  }
  return (
    <div>
      <GrupoChips etiqueta="Mostrar" className="mb-5" valor={estado} onCambiar={setEstado} opciones={[{ valor: 'NUEVO', texto: 'Nuevos' }, { valor: 'ATENDIDO', texto: 'Atendidos' }]} />
      <Alerta tipo="error" className="mb-4">{aviso}</Alerta>
      {cargando && <Cargando />}
      <Alerta tipo="error">{error?.message}</Alerta>
      {datos?.length === 0 && <Vacio>No hay mensajes.</Vacio>}
      <ul className="space-y-4">
        {datos?.map((c) => (
          <TarjetaModeracion
            key={c.id}
            titulo={c.asunto}
            meta={`${etiqueta('tipos_contacto', c.tipo)}${c.tipo === 'DENUNCIA' ? ' · prioridad alta' : ''}`}
            autor={`${c.nombre} · ${formatoFecha(c.created_at)}`}
          >
            <p className="mt-1 break-all text-[13px] text-lavanda">{c.email}</p>
            <p className="mt-3 whitespace-pre-line text-sm text-tinta">{c.mensaje}</p>
            {c.estado === 'NUEVO' && (
              <button className="boton-marca mt-4" onClick={() => atender(c)}>
                Marcar como respondido<span className="sr-only">: {c.asunto}</span>
              </button>
            )}
          </TarjetaModeracion>
        ))}
      </ul>
    </div>
  )
}
