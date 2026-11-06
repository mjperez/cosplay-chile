import { Link } from 'react-router-dom'

import { Etiqueta } from '../ui/Etiqueta'

export function Portada() {
  return (
    <section className="border-b border-tinta-200 bg-gradient-to-b from-marca-50 to-tinta-50">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:py-24">
        <div className="max-w-2xl">
          <Etiqueta tono="acento">Comunidad cosplay de Chile</Etiqueta>

          <h1 className="mt-5 text-4xl font-black leading-tight tracking-tight text-tinta-900 sm:text-5xl">
            Todo el cosplay chileno,{' '}
            <span className="text-marca-700">en un solo lugar</span>
          </h1>

          <p className="mt-5 text-lg leading-relaxed text-tinta-700">
            Encuentra cosmakers, sastres y fotógrafos por región. Aprende con guías
            de quienes ya pasaron por lo mismo. Y entérate de las convenciones y
            ferias antes de que se acaben los cupos.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              to="/registro"
              className="rounded-control bg-marca-700 px-6 py-3 text-base font-semibold text-white transition-colors hover:bg-marca-800"
            >
              Crear cuenta gratis
            </Link>
            <Link
              to="/ingresar"
              className="rounded-control border border-tinta-300 bg-white px-6 py-3 text-base font-semibold text-tinta-900 transition-colors hover:bg-tinta-100"
            >
              Ya tengo cuenta
            </Link>
          </div>

          <p className="mt-4 text-sm text-tinta-500">
            Sin costo. Solo pedimos tu correo para crear la cuenta.
          </p>
        </div>
      </div>
    </section>
  )
}
