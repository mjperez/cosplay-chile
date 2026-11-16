import { useState } from 'react'
import { api, qs } from '../../api/client'
import { useMeta } from '../../contexto/MetaContext'
import useApi from '../../components/useApi'
import { Alerta, Campo, Cargando, GrupoChips, Vacio } from '../../components/ui'

// Bloquear/Sancionar Usuario (extensión de Gestionar Soporte y Reportes, Fig. 10)
export default function Usuarios() {
  const { etiqueta } = useMeta()
  const [q, setQ] = useState('')
  const [estado, setEstado] = useState('')
  const { datos, error, cargando, recargar } = useApi(`/api/moderacion/usuarios${qs({ q, estado })}`)
  const [motivos, setMotivos] = useState({})
  const [aviso, setAviso] = useState(null)

  const accion = async (u, tipo) => {
    try {
      if (tipo === 'suspender') await api(`/api/moderacion/usuarios/${u.id}/suspender`, { method: 'POST', body: { motivo: motivos[u.id] || '' } })
      else await api(`/api/moderacion/usuarios/${u.id}/reactivar`, { method: 'POST' })
      setAviso({ tipo: 'exito', texto: tipo === 'suspender' ? `Suspendiste a ${u.nombre}.` : `Reactivaste a ${u.nombre}.` })
      recargar()
    } catch (e) {
      setAviso({ tipo: 'error', texto: e.campos?.motivo ? `Motivo: ${e.campos.motivo}` : e.message })
    }
  }

  return (
    <div>
      <div className="mb-5 flex flex-col gap-4">
        <Campo etiqueta="Buscar por nombre o correo" type="search" value={q} onChange={(e) => setQ(e.target.value)} className="max-w-md" />
        <GrupoChips etiqueta="Estado" valor={estado} onCambiar={setEstado} opciones={[{ valor: '', texto: 'Todas' }, { valor: 'ACTIVO', texto: 'Activas' }, { valor: 'SUSPENDIDO', texto: 'Suspendidas' }]} />
      </div>
      <Alerta tipo={aviso?.tipo} className="mb-4">{aviso?.texto}</Alerta>
      {cargando && <Cargando />}
      <Alerta tipo="error">{error?.message}</Alerta>
      {datos?.length === 0 && <Vacio>No hay cuentas con esos filtros.</Vacio>}
      <ul className="space-y-3">
        {datos?.map((u) => (
          <li key={u.id} className="panel flex flex-wrap items-end gap-4 p-5">
            <div className="min-w-48 flex-1">
              <p className="flex flex-wrap items-center gap-2 font-bold text-white">
                {u.nombre}
                {u.rol === 'ADMIN' && <span className="etiqueta text-xs">Moderación</span>}
                {u.estado === 'SUSPENDIDO' && <span className="insignia bg-peligro text-[#2a0606]">Suspendida</span>}
              </p>
              <p className="text-[13px] text-lavanda">{u.email} · {etiqueta('tipos_perfil', u.tipo_perfil)}</p>
              {u.estado === 'SUSPENDIDO' && <p className="mt-1 text-sm text-peligro">Motivo: {u.motivo_suspension}</p>}
            </div>
            {u.rol !== 'ADMIN' && u.estado === 'ACTIVO' && (
              <>
                <Campo
                  etiqueta={`Motivo para suspender a ${u.nombre}`}
                  className="min-w-56 flex-1"
                  value={motivos[u.id] || ''}
                  onChange={(e) => setMotivos((m) => ({ ...m, [u.id]: e.target.value }))}
                />
                <button className="boton-peligro" onClick={() => accion(u, 'suspender')}>Suspender<span className="sr-only"> a {u.nombre}</span></button>
              </>
            )}
            {u.estado === 'SUSPENDIDO' && (
              <button className="boton-contorno" onClick={() => accion(u, 'reactivar')}>Reactivar<span className="sr-only"> a {u.nombre}</span></button>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
