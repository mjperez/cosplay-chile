import { Link } from 'react-router-dom'

import { Etiqueta } from '../ui/Etiqueta'
import { Tarjeta } from '../ui/Tarjeta'

interface Modulo {
  nombre: string
  descripcion: string
  icono: React.ReactNode
  /** Presente solo si el módulo ya tiene pantalla. */
  to?: string
}

const MODULOS: Modulo[] = [
  {
    nombre: 'Directorio de profesionales',
    descripcion:
      'Cosmakers, sastres, fotógrafos y tiendas, filtrados por región y especialidad. Con portafolio y contacto directo.',
    to: '/directorio',
    icono: (
      <path
        d="M4 6h16M4 12h16M4 18h10"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    ),
  },
  {
    nombre: 'Contenidos y tutoriales',
    descripcion:
      'Guías paso a paso, entrevistas y artículos escritos por la propia comunidad. Filtradas por nivel de dificultad.',
    icono: (
      <path
        d="M4 5a2 2 0 0 1 2-2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5Zm10-2v6h6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    ),
  },
  {
    nombre: 'Calendario de eventos',
    descripcion:
      'Convenciones, concursos, ferias y talleres con fecha, lugar y enlace oficial. Sin rumores ni fechas viejas.',
    icono: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="2" />
        <path d="M8 3v4M16 3v4M3 11h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </>
    ),
  },
  {
    nombre: 'Comunidad y foro',
    descripcion:
      'Espacios por temática para resolver dudas, mostrar avances y coordinar grupos antes de una convención.',
    icono: (
      <path
        d="M21 12a8 8 0 0 1-8 8H7l-4 3v-7a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    ),
  },
]

export function Modulos() {
  return (
    <section aria-labelledby="titulo-modulos" className="mx-auto max-w-6xl px-4 py-16">
      <div className="max-w-2xl">
        <h2 id="titulo-modulos" className="text-2xl font-bold tracking-tight text-tinta-900 sm:text-3xl">
          Cuatro módulos, un mismo lugar
        </h2>
        <p className="mt-3 text-base text-tinta-600">
          Hoy la información está repartida entre grupos de Facebook, servidores de
          Discord y cuentas de Instagram. La plataforma la reúne y la mantiene al día.
        </p>
      </div>

      <ul className="mt-10 grid gap-5 sm:grid-cols-2">
        {MODULOS.map((modulo) => (
          <Tarjeta como="li" key={modulo.nombre} className="flex flex-col gap-3">
            <div className="flex items-start justify-between gap-3">
              <span
                aria-hidden="true"
                className="grid size-10 shrink-0 place-items-center rounded-control bg-marca-50 text-marca-700"
              >
                <svg viewBox="0 0 24 24" fill="none" className="size-5">
                  {modulo.icono}
                </svg>
              </span>
              {modulo.to ? (
                <Etiqueta tono="exito">Disponible</Etiqueta>
              ) : (
                <Etiqueta tono="neutro">Pronto</Etiqueta>
              )}
            </div>

            <h3 className="text-base font-semibold text-tinta-900">
              {modulo.to ? (
                <Link to={modulo.to} className="hover:text-marca-700 hover:underline">
                  {modulo.nombre}
                </Link>
              ) : (
                modulo.nombre
              )}
            </h3>
            <p className="text-sm leading-relaxed text-tinta-600">{modulo.descripcion}</p>

            {modulo.to && (
              <Link
                to={modulo.to}
                className="mt-auto text-sm font-semibold text-marca-700 hover:underline"
              >
                Ver el directorio
                <span aria-hidden="true"> →</span>
              </Link>
            )}
          </Tarjeta>
        ))}
      </ul>
    </section>
  )
}
