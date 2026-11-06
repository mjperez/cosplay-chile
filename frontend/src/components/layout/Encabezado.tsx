import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'

import { useAuth } from '../../lib/contextoAuth'
import { Boton } from '../ui/Boton'

/**
 * Módulos que todavía no tienen pantalla. Se muestran como texto con la marca
 * «pronto» en lugar de enlaces: un enlace que lleva a un 404 es peor que un
 * enlace que no existe, y T-02.3 pide verificar que no haya enlaces roscas.
 */
const MODULOS = [
  { nombre: 'Directorio', pronto: true },
  { nombre: 'Contenidos', pronto: true },
  { nombre: 'Eventos', pronto: true },
  { nombre: 'Comunidad', pronto: true },
]

export function Encabezado() {
  const { usuario, cerrarSesion } = useAuth()
  const [abierto, setAbierto] = useState(false)

  return (
    <header className="sticky top-0 z-40 border-b border-tinta-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link
          to="/"
          className="flex items-center gap-2 rounded-control font-bold tracking-tight text-tinta-900"
        >
          <span
            aria-hidden="true"
            className="grid size-8 place-items-center rounded-control bg-marca-700 text-sm font-black text-white"
          >
            CC
          </span>
          <span className="text-base">Cosplay Chile</span>
        </Link>

        {/* El menú completo no cabe a 768 px: cinco módulos más el logo y los
            botones de sesión suman más de 900 px. Por eso el corte es lg
            (1024 px) y no md. */}
        <nav aria-label="Navegación principal" className="hidden lg:block">
          <ul className="flex items-center gap-1">
            <li>
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  [
                    'rounded-control px-3 py-2 text-sm font-medium',
                    isActive
                      ? 'bg-marca-50 text-marca-800'
                      : 'text-tinta-700 hover:bg-tinta-100',
                  ].join(' ')
                }
              >
                Inicio
              </NavLink>
            </li>
            {MODULOS.map((modulo) => (
              <li key={modulo.nombre}>
                <span
                  aria-disabled="true"
                  className="flex cursor-not-allowed items-center gap-1.5 rounded-control px-3 py-2 text-sm font-medium text-tinta-400"
                >
                  {modulo.nombre}
                  <span className="rounded-full bg-tinta-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-tinta-500">
                    pronto
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          {usuario ? (
            <>
              <span className="text-sm text-tinta-600">
                Hola, <strong className="font-semibold text-tinta-900">{usuario.nombre}</strong>
              </span>
              <Boton variante="secundario" tamano="sm" onClick={cerrarSesion}>
                Salir
              </Boton>
            </>
          ) : (
            <>
              <Link
                to="/ingresar"
                className="rounded-control px-3 py-2 text-sm font-medium text-tinta-700 hover:bg-tinta-100"
              >
                Ingresar
              </Link>
              <Link
                to="/registro"
                className="rounded-control bg-marca-700 px-3 py-2 text-sm font-semibold text-white hover:bg-marca-800"
              >
                Crear cuenta
              </Link>
            </>
          )}
        </div>

        <button
          type="button"
          className="rounded-control border border-tinta-300 px-3 py-2 text-sm font-medium lg:hidden"
          aria-expanded={abierto}
          aria-controls="menu-movil"
          onClick={() => setAbierto((valor) => !valor)}
        >
          {abierto ? 'Cerrar' : 'Menú'}
        </button>
      </div>

      {abierto && (
        <div id="menu-movil" className="border-t border-tinta-200 bg-white lg:hidden">
          <nav aria-label="Navegación principal móvil" className="mx-auto max-w-6xl px-4 py-3">
            <ul className="flex flex-col gap-1">
              <li>
                <NavLink
                  to="/"
                  end
                  onClick={() => setAbierto(false)}
                  className="block rounded-control px-3 py-2 text-sm font-medium text-tinta-700 hover:bg-tinta-100"
                >
                  Inicio
                </NavLink>
              </li>
              {MODULOS.map((modulo) => (
                <li key={modulo.nombre}>
                  <span
                    aria-disabled="true"
                    className="flex cursor-not-allowed items-center gap-2 rounded-control px-3 py-2 text-sm text-tinta-400"
                  >
                    {modulo.nombre}
                    <span className="rounded-full bg-tinta-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-tinta-500">
                      pronto
                    </span>
                  </span>
                </li>
              ))}
              <li className="mt-2 border-t border-tinta-200 pt-2">
                {usuario ? (
                  <button
                    type="button"
                    onClick={() => {
                      cerrarSesion()
                      setAbierto(false)
                    }}
                    className="w-full rounded-control px-3 py-2 text-left text-sm font-medium text-tinta-700 hover:bg-tinta-100"
                  >
                    Cerrar sesión
                  </button>
                ) : (
                  <div className="flex flex-col gap-2">
                    <Link
                      to="/ingresar"
                      onClick={() => setAbierto(false)}
                      className="rounded-control border border-tinta-300 px-3 py-2 text-center text-sm font-medium"
                    >
                      Ingresar
                    </Link>
                    <Link
                      to="/registro"
                      onClick={() => setAbierto(false)}
                      className="rounded-control bg-marca-700 px-3 py-2 text-center text-sm font-semibold text-white"
                    >
                      Crear cuenta
                    </Link>
                  </div>
                )}
              </li>
            </ul>
          </nav>
        </div>
      )}
    </header>
  )
}
