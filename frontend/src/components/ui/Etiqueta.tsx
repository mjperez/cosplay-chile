import type { ReactNode } from 'react'

type Tono = 'marca' | 'acento' | 'neutro' | 'exito'

const TONOS: Record<Tono, string> = {
  marca: 'bg-marca-100 text-marca-800',
  acento: 'bg-acento-100 text-acento-700',
  neutro: 'bg-tinta-100 text-tinta-700',
  exito: 'bg-emerald-100 text-exito-600',
}

interface Props {
  children: ReactNode
  tono?: Tono
}

export function Etiqueta({ children, tono = 'marca' }: Props) {
  return (
    <span
      className={[
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
        TONOS[tono],
      ].join(' ')}
    >
      {children}
    </span>
  )
}
