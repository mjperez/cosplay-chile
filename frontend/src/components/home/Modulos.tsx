import { Link } from 'react-router-dom'

import { Etiqueta } from '../ui/Etiqueta'
import { Tarjeta } from '../ui/Tarjeta'

interface Modulo {
  nombre: string
  descripcion: string
  to: string
  llamada: string
  icono: React.ReactNode
}

const MODULOS: Modulo[] = [
  {
    nombre: 'Directorio de profesionales',
    descripcion:
      'Cosmakers, sastres, fotógrafos y tiendas, filtrados por región y especialidad. Con portafolio y contacto directo.',
    to: '/directorio',
    llamada: 'Ver el directorio',
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
    to: '/contenido',
    llamada: 'Leer contenidos',
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
      'Convenciones, concursos, ferias y talleres con fecha, lugar y enlace oficial. Inscríbete y cuenta con qué personaje vas.',
    to: '/eventos',
    llamada: 'Ver el calendario',
    icono: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="2" />
        <path d="M8 3v4M16 3v4M3 11h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </>
    ),
  },
  {
    nombre: 'Foro de la comunidad',
    descripcion:
      'Espacios por temática para resolver dudas, mostrar avances y coordinar grupos antes de una convención.',
    to: '/foro',
    llamada: 'Entrar al foro',
    icono: (
      <path
        d="M21 12a8 8 0 0 1-8 8H7l-4 3v-7a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    ),
  },
  {
    nombre: 'Desafío mensual',
    descripcion:
      'Un reto distinto cada mes y un ganador elegido por la comunidad. Mira el desafío vigente y el historial.',
    to: '/desafios',
    llamada: 'Ver el desafío',
    icono: (
      <path
        d="M8 4h8v4a4 4 0 0 1-8 0V4Zm0 2H4v2a4 4 0 0 0 4 4m8-6h4v2a4 4 0 0 1-4 4m-4 4v4m-3 2h6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
  },
  {
    nombre: 'Dónde comprar y grupos',
    descripcion:
      'Tiendas de materiales que envían a Chile, grupos regionales y tu perfil público de cosplayer.',
    to: '/comunidad',
    llamada: 'Explorar la comunidad',
    icono: (
      <path
        d="M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m7-10a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm13 10v-2a4 4 0 0 0-3-3.87M16 4.13a4 4 0 0 1 0 7.75"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
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
          Seis módulos, un mismo lugar
        </h2>
        <p className="mt-3 text-base text-tinta-600">
          Hoy la información está repartida entre grupos de Facebook, servidores de
          Discord y cuentas de Instagram. La plataforma la reúne y la mantiene al día.
        </p>
      </div>

      <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
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
              <Etiqueta tono="exito">Disponible</Etiqueta>
            </div>

            <h3 className="text-base font-semibold text-tinta-900">
              <Link to={modulo.to} className="hover:text-marca-700 hover:underline">
                {modulo.nombre}
              </Link>
            </h3>
            <p className="text-sm leading-relaxed text-tinta-600">{modulo.descripcion}</p>

            <Link
              to={modulo.to}
              className="mt-auto text-sm font-semibold text-marca-700 hover:underline"
            >
              {modulo.llamada}
              <span aria-hidden="true"> →</span>
            </Link>
          </Tarjeta>
        ))}
      </ul>
    </section>
  )
}
