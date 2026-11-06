import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variante = 'primario' | 'secundario' | 'fantasma'
type Tamano = 'sm' | 'md' | 'lg'

const VARIANTES: Record<Variante, string> = {
  primario:
    'bg-marca-700 text-white hover:bg-marca-800 active:bg-marca-900 disabled:bg-tinta-300 disabled:text-tinta-500',
  secundario:
    'border border-tinta-300 bg-white text-tinta-900 hover:bg-tinta-100 disabled:text-tinta-400',
  fantasma:
    'text-marca-700 hover:bg-marca-50 disabled:text-tinta-400',
}

const TAMANOS: Record<Tamano, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
}

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variante
  tamano?: Tamano
  cargando?: boolean
  children: ReactNode
}

export function Boton({
  variante = 'primario',
  tamano = 'md',
  cargando = false,
  className = '',
  children,
  disabled,
  ...resto
}: Props) {
  return (
    <button
      {...resto}
      disabled={disabled || cargando}
      aria-busy={cargando || undefined}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-control font-semibold',
        'transition-colors duration-150',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600',
        'disabled:cursor-not-allowed',
        VARIANTES[variante],
        TAMANOS[tamano],
        className,
      ].join(' ')}
    >
      {cargando && (
        <span
          aria-hidden="true"
          className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      )}
      {children}
    </button>
  )
}
