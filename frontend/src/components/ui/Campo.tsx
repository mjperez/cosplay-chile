import type { InputHTMLAttributes, ReactNode } from 'react'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  etiqueta: string
  ayuda?: string
  error?: string
  children?: ReactNode
}

/**
 * Campo de formulario con etiqueta asociada, texto de ayuda y mensaje de error.
 *
 * El error se anuncia a lectores de pantalla con `role="alert"` y se enlaza al
 * input con `aria-describedby`, no solo con color: un borde rojo no comunica
 * nada a quien no distingue colores.
 */
export function Campo({
  etiqueta,
  ayuda,
  error,
  id,
  children,
  className = '',
  ...resto
}: Props) {
  const idCampo = id ?? `campo-${etiqueta.toLowerCase().replace(/\s+/g, '-')}`
  const idAyuda = ayuda ? `${idCampo}-ayuda` : undefined
  const idError = error ? `${idCampo}-error` : undefined
  const descrito = [idAyuda, idError].filter(Boolean).join(' ') || undefined

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={idCampo} className="text-sm font-medium text-tinta-800">
        {etiqueta}
      </label>

      <input
        {...resto}
        id={idCampo}
        aria-invalid={error ? true : undefined}
        aria-describedby={descrito}
        className={[
          'rounded-control border bg-white px-3 py-2.5 text-sm text-tinta-900',
          'placeholder:text-tinta-400',
          'focus-visible:outline-2 focus-visible:outline-offset-2',
          error
            ? 'border-error-600 focus-visible:outline-error-600'
            : 'border-tinta-300 focus-visible:outline-marca-600',
          className,
        ].join(' ')}
      />

      {ayuda && (
        <p id={idAyuda} className="text-xs text-tinta-500">
          {ayuda}
        </p>
      )}

      {error && (
        <p id={idError} role="alert" className="text-xs font-medium text-error-600">
          {error}
        </p>
      )}

      {children}
    </div>
  )
}
