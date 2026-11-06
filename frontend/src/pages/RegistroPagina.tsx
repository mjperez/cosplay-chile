import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Campo } from '../components/ui/Campo'
import { api, ErrorApi, type PoliticaPrivacidad, type Rol } from '../lib/api'
import { useAuth } from '../lib/contextoAuth'

const REGIONES = [
  'Arica y Parinacota',
  'Tarapacá',
  'Antofagasta',
  'Atacama',
  'Coquimbo',
  'Valparaíso',
  'Metropolitana',
  "O'Higgins",
  'Maule',
  'Ñuble',
  'Biobío',
  'La Araucanía',
  'Los Ríos',
  'Los Lagos',
  'Aysén',
  'Magallanes',
]

const ROLES: { valor: Exclude<Rol, 'administrador'>; etiqueta: string }[] = [
  { valor: 'cosplayer', etiqueta: 'Cosplayer' },
  { valor: 'cosmaker', etiqueta: 'Cosmaker' },
  { valor: 'sastre', etiqueta: 'Sastre' },
  { valor: 'tienda', etiqueta: 'Tienda' },
  { valor: 'fotografo', etiqueta: 'Fotógrafo' },
  { valor: 'organizador', etiqueta: 'Organizador de eventos' },
  { valor: 'visitante', etiqueta: 'Solo quiero explorar' },
]

export function RegistroPagina() {
  const { registrar } = useAuth()
  const navegar = useNavigate()

  const [politica, setPolitica] = useState<PoliticaPrivacidad | null>(null)
  const [nombre, setNombre] = useState('')
  const [correo, setCorreo] = useState('')
  const [password, setPassword] = useState('')
  const [rol, setRol] = useState<Exclude<Rol, 'administrador'>>('cosplayer')
  const [region, setRegion] = useState('Metropolitana')
  const [acepta, setAcepta] = useState(false)
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  // La versión del consentimiento no se escribe a mano: se pide al backend.
  // Si el texto cambia, el formulario se entera solo.
  useEffect(() => {
    api
      .politica()
      .then(setPolitica)
      .catch(() => setError('No pudimos cargar la política de privacidad.'))
  }, [])

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    setError('')

    if (!acepta) {
      setError('Tienes que aceptar la política de privacidad para crear la cuenta.')
      return
    }
    if (!politica) {
      setError('Todavía no cargó la política de privacidad. Espera un momento.')
      return
    }

    setEnviando(true)
    try {
      await registrar({
        nombre: nombre.trim(),
        correo: correo.trim(),
        password,
        rol,
        region,
        acepta_privacidad: true,
        consentimiento_version: politica.version,
      })
      navegar('/', { replace: true })
    } catch (fallo) {
      if (fallo instanceof ErrorApi && fallo.estado === 409) {
        setError('Ese correo ya tiene una cuenta. Prueba ingresando.')
      } else if (fallo instanceof ErrorApi) {
        setError(fallo.message)
      } else {
        setError('No pudimos conectar con el servidor. Revisa tu conexión.')
      }
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Disposicion>
      <div className="mx-auto w-full max-w-lg px-4 py-16">
        <h1 className="text-2xl font-bold tracking-tight text-tinta-900">Crear cuenta</h1>
        <p className="mt-2 text-sm text-tinta-600">
          Toma menos de un minuto. Puedes cambiar tu perfil después.
        </p>

        <form onSubmit={enviar} className="mt-8 flex flex-col gap-5" noValidate>
          <Campo
            etiqueta="Nombre"
            id="nombre"
            autoComplete="name"
            required
            minLength={2}
            value={nombre}
            onChange={(evento) => setNombre(evento.target.value)}
          />

          <Campo
            etiqueta="Correo electrónico"
            id="correo"
            type="email"
            autoComplete="email"
            required
            ayuda="Lo usas para entrar. No se muestra en tu perfil público."
            value={correo}
            onChange={(evento) => setCorreo(evento.target.value)}
          />

          <Campo
            etiqueta="Contraseña"
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            ayuda="Mínimo 8 caracteres."
            value={password}
            onChange={(evento) => setPassword(evento.target.value)}
          />

          <div className="flex flex-col gap-1.5">
            <label htmlFor="rol" className="text-sm font-medium text-tinta-800">
              ¿Cómo participas?
            </label>
            <select
              id="rol"
              value={rol}
              onChange={(evento) => setRol(evento.target.value as Exclude<Rol, 'administrador'>)}
              className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
            >
              {ROLES.map((opcion) => (
                <option key={opcion.valor} value={opcion.valor}>
                  {opcion.etiqueta}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="region" className="text-sm font-medium text-tinta-800">
              Región
            </label>
            <select
              id="region"
              value={region}
              onChange={(evento) => setRegion(evento.target.value)}
              className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
            >
              {REGIONES.map((nombreRegion) => (
                <option key={nombreRegion} value={nombreRegion}>
                  {nombreRegion}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-start gap-3 rounded-control bg-tinta-100 p-4">
            <input
              id="acepta"
              type="checkbox"
              checked={acepta}
              onChange={(evento) => setAcepta(evento.target.checked)}
              className="mt-0.5 size-4 rounded border-tinta-300 text-marca-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
            />
            <label htmlFor="acepta" className="text-sm leading-relaxed text-tinta-700">
              Acepto la{' '}
              <Link to="/privacidad" className="font-semibold text-marca-700 hover:underline">
                política de privacidad
              </Link>
              {politica && (
                <span className="text-tinta-500"> (versión {politica.version})</span>
              )}
              .
            </label>
          </div>

          {error && (
            <p role="alert" className="rounded-control bg-error-50 px-3 py-2 text-sm font-medium text-error-600">
              {error}
            </p>
          )}

          <Boton type="submit" cargando={enviando} tamano="lg">
            {enviando ? 'Creando cuenta' : 'Crear cuenta'}
          </Boton>
        </form>

        <p className="mt-6 text-sm text-tinta-600">
          ¿Ya tienes cuenta?{' '}
          <Link to="/ingresar" className="font-semibold text-marca-700 hover:underline">
            Ingresa aquí
          </Link>
          .
        </p>
      </div>
    </Disposicion>
  )
}
