import type { ReactNode } from 'react'

import { Encabezado } from './Encabezado'
import { Pie } from './Pie'

/**
 * Armazón compartido por todas las páginas.
 *
 * El primer elemento del documento es un enlace de salto: quien navega con
 * teclado puede saltarse el menú completo sin recorrerlo en cada página.
 */
export function Disposicion({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <a href="#contenido" className="saltar-al-contenido">
        Saltar al contenido
      </a>
      <Encabezado />
      <main id="contenido" className="flex-1">
        {children}
      </main>
      <Pie />
    </div>
  )
}
