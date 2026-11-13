import { Link } from 'react-router-dom'

export function Pie() {
  return (
    <footer className="mt-20 border-t border-tinta-200 bg-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <p className="text-sm font-bold text-tinta-900">Cosplay Chile</p>
          <p className="mt-2 max-w-xs text-sm text-tinta-600">
            Plataforma de contenidos, directorio y comunidad para el cosplay chileno.
          </p>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-tinta-500">
            Plataforma
          </p>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <Link to="/" className="text-tinta-700 hover:text-marca-700">
                Inicio
              </Link>
            </li>
            <li>
              <Link to="/registro" className="text-tinta-700 hover:text-marca-700">
                Crear cuenta
              </Link>
            </li>
            <li>
              <Link to="/ingresar" className="text-tinta-700 hover:text-marca-700">
                Ingresar
              </Link>
            </li>
            <li>
              <Link to="/perfil" className="text-tinta-700 hover:text-marca-700">
                Mi perfil
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-tinta-500">
            Módulos
          </p>
          <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <li>
              <Link to="/directorio" className="text-tinta-700 hover:text-marca-700">
                Directorio
              </Link>
            </li>
            <li>
              <Link to="/contenido" className="text-tinta-700 hover:text-marca-700">
                Contenidos
              </Link>
            </li>
            <li>
              <Link to="/eventos" className="text-tinta-700 hover:text-marca-700">
                Eventos
              </Link>
            </li>
            <li>
              <Link to="/foro" className="text-tinta-700 hover:text-marca-700">
                Foro
              </Link>
            </li>
            <li>
              <Link to="/desafios" className="text-tinta-700 hover:text-marca-700">
                Desafíos
              </Link>
            </li>
            <li>
              <Link to="/comunidad" className="text-tinta-700 hover:text-marca-700">
                Comunidad
              </Link>
            </li>
            <li>
              <Link to="/privacidad" className="text-tinta-700 hover:text-marca-700">
                Privacidad
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-tinta-200 py-4">
        <p className="mx-auto max-w-6xl px-4 text-xs text-tinta-500">
          Proyecto de TI3043 · Ingeniería de Software · INACAP · 2026
        </p>
      </div>
    </footer>
  )
}
