import useApi from '../../components/useApi'
import { Alerta, Cargando, Vacio } from '../../components/ui'

// Registros escritos por RegistroAuditoriaObserver (patrón Observer)
export default function Bitacora() {
  const { datos, error, cargando } = useApi('/api/moderacion/auditoria?limite=100')
  return (
    <div>
      <p className="mb-4 text-sm text-lavanda">Cada acción relevante queda registrada automáticamente por el observador de auditoría.</p>
      {cargando && <Cargando />}
      <Alerta tipo="error">{error?.message}</Alerta>
      {datos?.length === 0 && <Vacio>Sin registros todavía.</Vacio>}
      {datos?.length > 0 && (
        <div className="panel overflow-x-auto">
          <table className="w-full min-w-[40rem] border-collapse text-sm">
            <caption className="sr-only">Bitácora de auditoría</caption>
            <thead>
              <tr className="border-b border-white/16 text-left">
                {['Fecha', 'Evento', 'Quién', 'Detalle'].map((h) => (
                  <th key={h} scope="col" className="p-3 text-xs font-bold uppercase tracking-[.14em] text-durazno">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {datos.map((a) => (
                <tr key={a.id} className="border-b border-white/10 align-top last:border-b-0">
                  <td className="whitespace-nowrap p-3 text-lavanda">{new Date(a.created_at).toLocaleString('es-CL', { dateStyle: 'short', timeStyle: 'short' })}</td>
                  <td className="p-3 font-mono text-xs text-white">{a.evento}</td>
                  <td className="p-3 text-white">{a.actor?.nombre || 'Sistema'}</td>
                  <td className="p-3 text-xs text-lavanda">
                    {Object.entries(a.detalle || {}).filter(([k]) => !k.endsWith('_id')).map(([k, v]) => `${k}: ${v}`).join(' · ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
