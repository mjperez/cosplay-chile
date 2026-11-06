import { useEffect, useState } from 'react'

import { Disposicion } from '../components/layout/Disposicion'
import { api, type PoliticaPrivacidad } from '../lib/api'

export function PrivacidadPagina() {
  const [politica, setPolitica] = useState<PoliticaPrivacidad | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .politica()
      .then(setPolitica)
      .catch(() => setError('No pudimos cargar la política. Intenta recargar la página.'))
  }, [])

  return (
    <Disposicion>
      <div className="mx-auto max-w-2xl px-4 py-16">
        <h1 className="text-2xl font-bold tracking-tight text-tinta-900">
          {politica?.titulo ?? 'Política de privacidad'}
        </h1>

        {politica && (
          <p className="mt-2 text-sm text-tinta-500">
            Versión {politica.version} · {politica.fecha}
          </p>
        )}

        {error && (
          <p role="alert" className="mt-6 rounded-control bg-error-50 px-3 py-2 text-sm text-error-600">
            {error}
          </p>
        )}

        {politica && (
          <div className="mt-8 space-y-4 text-sm leading-relaxed text-tinta-700">
            {politica.texto.split('\n\n').map((parrafo, indice) => (
              <p key={indice}>{parrafo}</p>
            ))}
          </div>
        )}

        {!politica && !error && <p className="mt-8 text-sm text-tinta-500">Cargando…</p>}
      </div>
    </Disposicion>
  )
}
