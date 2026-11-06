import { Link } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'

export function NoEncontradaPagina() {
  return (
    <Disposicion>
      <div className="mx-auto max-w-lg px-4 py-24 text-center">
        <p className="text-sm font-semibold uppercase tracking-wide text-marca-700">Error 404</p>
        <h1 className="mt-3 text-3xl font-black tracking-tight text-tinta-900">
          Esta página no existe
        </h1>
        <p className="mt-3 text-base text-tinta-600">
          Puede que el enlace esté mal escrito o que la sección todavía no esté
          disponible.
        </p>
        <Link
          to="/"
          className="mt-8 inline-block rounded-control bg-marca-700 px-6 py-3 text-base font-semibold text-white hover:bg-marca-800"
        >
          Volver al inicio
        </Link>
      </div>
    </Disposicion>
  )
}
