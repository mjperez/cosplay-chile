import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  className?: string
  /** `article` cuando la tarjeta es una unidad de contenido con sentido propio. */
  como?: 'div' | 'article' | 'li'
}

export function Tarjeta({ children, className = '', como: Etiqueta = 'div' }: Props) {
  return (
    <Etiqueta
      className={[
        'rounded-tarjeta border border-tinta-200 bg-white p-6',
        'shadow-[0_1px_2px_rgba(28,25,23,0.04)]',
        className,
      ].join(' ')}
    >
      {children}
    </Etiqueta>
  )
}
