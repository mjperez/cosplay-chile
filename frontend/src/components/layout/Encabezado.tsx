import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'

import { useAuth } from '../../lib/contextoAuth'
import { Boton } from '../ui/Boton'

/** Módulos de la plataforma. Todos tienen pantalla implementada. */
const MODULOS: { nombre: string; to: string }[] = [
  { nombre: 'Directorio', to: '/directorio' },
  { nombre: 'Contenidos', to: '/contenido' },
  { nombre: 'Eventos', to: '/eventos' },
  { nombre: 'Foro', to: '/foro' },
  { nombre: 'Desafíos', to: '/desafios' },
  { nombre: 'Comunidad', to: '/comunidad' },
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

        {/* Con siete módulos, el menú completo más el logo y los botones de
            sesión supera los 1024 px. El corte es xl (1280 px); por debajo se
            usa el menú móvil, que tiene exactamente las mismas rutas. */}
        <nav aria-label="Navegación principal" className="hidden xl:block">
          <ul className="flex items-center gap-0.5">
            <li>
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  [
                    'rounded-control px-2.5 py-2 text-sm font-medium',
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
                <NavLink
                  to={modulo.to}
                  className={({ isActive }) =>
                    [
                      'rounded-control px-2.5 py-2 text-sm font-medium',
                      isActive
                        ? 'bg-marca-50 text-marca-800'
                        : 'text-tinta-700 hover:bg-tinta-100',
                    ].join(' ')
                  }
                >
                  {modulo.nombre}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="hidden items-center gap-2 xl:flex">
          {usuario ? (
            <>
              <Link
                to="/perfil"
                className="rounded-control px-2.5 py-2 text-sm font-medium text-tinta-700 hover:bg-tinta-100"
              >
                Mi perfil
              </Link>
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
          className="rounded-control border border-tinta-300 px-3 py-2 text-sm font-medium xl:hidden"
          aria-expanded={abierto}
          aria-controls="menu-movil"
          onClick={() => setAbierto((valor) => !valor)}
        >
          {abierto ? 'Cerrar' : 'Menú'}
        </button>
      </div>

      {abierto && (
        <div id="menu-movil" className="border-t border-tinta-200 bg-white xl:hidden">
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
                  <NavLink
                    to={modulo.to}
                    onClick={() => setAbierto(false)}
                    className="block rounded-control px-3 py-2 text-sm font-medium text-tinta-700 hover:bg-tinta-100"
                  >
                    {modulo.nombre}
                  </NavLink>
                </li>
              ))}
              <li className="mt-2 border-t border-tinta-200 pt-2">
                {usuario ? (
                  <div className="flex flex-col gap-1">
                    <Link
                      to="/perfil"
                      onClick={() => setAbierto(false)}
                      className="block rounded-control px-3 py-2 text-sm font-medium text-tinta-700 hover:bg-tinta-100"
                    >
                      Mi perfil
                    </Link>
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
                  </div>
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
