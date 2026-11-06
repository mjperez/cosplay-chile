import { Link } from 'react-router-dom'

const PASOS = [
  {
    titulo: 'Crea tu cuenta',
    detalle:
      'Nombre, correo y región. Eliges el rol con el que participas: cosplayer, cosmaker, sastre, tienda, fotógrafo u organizador.',
  },
  {
    titulo: 'Completa tu perfil',
    detalle:
      'Si ofreces servicios, agregas especialidad y portafolio. Si solo participas, con tu región basta para que te ubiquen.',
  },
  {
    titulo: 'Participa',
    detalle:
      'Publicas una guía, te anotas en un evento o contactas a un proveedor. Todo queda en la misma cuenta.',
  },
]

export function Pasos() {
  return (
    <section aria-labelledby="titulo-pasos" className="border-y border-tinta-200 bg-white">
      <div className="mx-auto max-w-6xl px-4 py-16">
        <h2 id="titulo-pasos" className="text-2xl font-bold tracking-tight text-tinta-900 sm:text-3xl">
          Cómo funciona
        </h2>
        <p className="mt-3 max-w-2xl text-base text-tinta-600">
          Tres pasos. No hay periodo de espera ni invitación: la cuenta queda activa
          apenas la creas.
        </p>

        <ol className="mt-10 grid gap-6 sm:grid-cols-3">
          {PASOS.map((paso, indice) => (
            <li key={paso.titulo} className="flex flex-col gap-2">
              <span
                aria-hidden="true"
                className="grid size-9 place-items-center rounded-full bg-marca-700 text-sm font-bold text-white"
              >
                {indice + 1}
              </span>
              <h3 className="text-base font-semibold text-tinta-900">{paso.titulo}</h3>
              <p className="text-sm leading-relaxed text-tinta-600">{paso.detalle}</p>
            </li>
          ))}
        </ol>

        <div className="mt-12 rounded-tarjeta bg-marca-900 px-6 py-10 text-center">
          <h2 className="text-xl font-bold text-white sm:text-2xl">
            ¿Te sumas al directorio?
          </h2>
          <p className="mx-auto mt-2 max-w-lg text-sm text-marca-200">
            Si ofreces servicios de cosplay en Chile, crear la cuenta toma menos de un
            minuto.
          </p>
          <Link
            to="/registro"
            className="mt-6 inline-block rounded-control bg-white px-6 py-3 text-base font-semibold text-marca-900 transition-colors hover:bg-marca-100"
          >
            Crear cuenta
          </Link>
        </div>
      </div>
    </section>
  )
}
