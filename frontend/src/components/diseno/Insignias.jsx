import { useMeta } from '../../contexto/MetaContext'

const NIVEL = {
  PRINCIPIANTE: 'bg-nivel-principiante text-[#06281a]',
  INTERMEDIO: 'bg-nivel-intermedio text-[#2a1c00]',
  AVANZADO: 'bg-nivel-avanzado text-[#2a0617]',
}

const EVENTO = {
  CONVENCION: 'bg-evento-convencion text-[#2a0617]',
  CONCURSO: 'bg-evento-concurso text-[#2a1c00]',
  MEETUP: 'bg-evento-meetup text-[#05282e]',
  TALLER: 'bg-evento-taller text-[#052816]',
}
export const COLOR_EVENTO = {
  CONVENCION: 'bg-evento-convencion',
  CONCURSO: 'bg-evento-concurso',
  MEETUP: 'bg-evento-meetup',
  TALLER: 'bg-evento-taller',
}

export function InsigniaNivel({ nivel, className = '' }) {
  const { etiqueta } = useMeta()
  return <span className={`insignia ${NIVEL[nivel] || 'bg-white text-tinta-oscura'} ${className}`}>{etiqueta('niveles', nivel)}</span>
}

export function InsigniaEvento({ tipo, className = '' }) {
  const { etiqueta } = useMeta()
  return <span className={`insignia ${EVENTO[tipo] || 'bg-white text-tinta-oscura'} ${className}`}>{etiqueta('tipos_evento', tipo)}</span>
}
