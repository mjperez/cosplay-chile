import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Campo } from '../components/ui/Campo'
import { ErrorApi } from '../lib/api'
import { useAuth } from '../lib/contextoAuth'

interface EstadoNavegacion {
  desde?: string
}

export function IngresarPagina() {
  const { iniciarSesion } = useAuth()
  const navegar = useNavigate()
  const ubicacion = useLocation()

  const [correo, setCorreo] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  const destino = (ubicacion.state as EstadoNavegacion | null)?.desde ?? '/'

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    setError('')
    setEnviando(true)
    try {
      await iniciarSesion(correo, password)
      navegar(destino, { replace: true })
    } catch (fallo) {
      if (fallo instanceof ErrorApi && fallo.estado === 429) {
        setError('Demasiados intentos fallidos. Espera unos minutos antes de reintentar.')
      } else if (fallo instanceof ErrorApi && fallo.estado === 401) {
        setError('Correo o contraseña incorrectos.')
      } else {
        setError('No pudimos conectar con el servidor. Revisa tu conexión.')
      }
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Disposicion>
      <div className="mx-auto w-full max-w-md px-4 py-16">
        <h1 className="text-2xl font-bold tracking-tight text-tinta-900">Ingresar</h1>
        <p className="mt-2 text-sm text-tinta-600">
          Entra con el correo y la contraseña que usaste al crear la cuenta.
        </p>

        <form onSubmit={enviar} className="mt-8 flex flex-col gap-5" noValidate>
          <Campo
            etiqueta="Correo electrónico"
            id="correo"
            type="email"
            autoComplete="email"
            required
            value={correo}
            onChange={(evento) => setCorreo(evento.target.value)}
          />

          <Campo
            etiqueta="Contraseña"
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(evento) => setPassword(evento.target.value)}
          />

          {error && (
            <p role="alert" className="rounded-control bg-error-50 px-3 py-2 text-sm font-medium text-error-600">
              {error}
            </p>
          )}

          <Boton type="submit" cargando={enviando} tamano="lg">
            {enviando ? 'Ingresando' : 'Ingresar'}
          </Boton>
        </form>

        <p className="mt-6 text-sm text-tinta-600">
          ¿No tienes cuenta?{' '}
          <Link to="/registro" className="font-semibold text-marca-700 hover:underline">
            Créala aquí
          </Link>
          .
        </p>
      </div>
    </Disposicion>
  )
}
