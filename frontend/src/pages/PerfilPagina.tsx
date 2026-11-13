import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Campo } from '../components/ui/Campo'
import { Etiqueta } from '../components/ui/Etiqueta'
import { Tarjeta } from '../components/ui/Tarjeta'
import { ErrorApi } from '../lib/api'
import { useAuth } from '../lib/contextoAuth'
import {
  REGIONES_CHILE,
  enlaceExterno,
  mensajeDeFallo,
  modulosApi,
  type DatosPerfil,
  type Perfil,
} from '../lib/modulos'

/** Perfil propio: lectura y edición. Sin sesión, invitación a ingresar. */
export function PerfilPagina() {
  const { usuario, cargando: cargandoAuth } = useAuth()

  const [perfil, setPerfil] = useState<Perfil | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [reintento, setReintento] = useState(0)

  const [editando, setEditando] = useState(false)
  const [especialidad, setEspecialidad] = useState('')
  const [portafolioUrl, setPortafolioUrl] = useState('')
  const [biografia, setBiografia] = useState('')
  const [region, setRegion] = useState('')
  const [guardando, setGuardando] = useState(false)
  const [errorFormulario, setErrorFormulario] = useState('')
  const [aviso, setAviso] = useState('')

  useEffect(() => {
    if (!usuario) return
    let vigente = true
    // El reinicio va en microtarea para no provocar un render en cascada
    // dentro del effect (regla de React Compiler).
    queueMicrotask(() => {
      if (!vigente) return
      setCargando(true)
      setError('')
      modulosApi
        .perfilPropio()
        .then((datosPerfil) => {
          if (!vigente) return
          setPerfil(datosPerfil)
          setCargando(false)
        })
        .catch((fallo: unknown) => {
          if (!vigente) return
          if (fallo instanceof ErrorApi && fallo.estado === 401) {
            setError('Tu sesión venció. Vuelve a ingresar para ver tu perfil.')
          } else {
            setError(mensajeDeFallo(fallo, 'No pudimos cargar tu perfil. Revisa tu conexión.'))
          }
          setCargando(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [usuario, reintento])

  // No hay un effect que copie `perfil` al formulario: `abrirEdicion()` ya
  // toma los valores frescos cada vez que se abre, y así no se sobrescribe
  // lo que el usuario está escribiendo si el perfil se recarga de fondo.
  function abrirEdicion() {
    if (!perfil) return
    setEspecialidad(perfil.especialidad ?? '')
    setPortafolioUrl(perfil.portafolio_url ?? '')
    setBiografia(perfil.biografia ?? '')
    setRegion(perfil.region ?? '')
    setAviso('')
    setErrorFormulario('')
    setEditando(true)
  }

  async function guardar(formulario: FormEvent) {
    formulario.preventDefault()
    setErrorFormulario('')
    setAviso('')

    // La cadena vacía es una decisión explícita: «prefiero no indicar la
    // región». El backend la guarda tal cual en lugar de volver a tomar la
    // región de la cuenta.
    const datos: DatosPerfil = {
      especialidad: especialidad.trim() || null,
      portafolio_url: portafolioUrl.trim() || null,
      biografia: biografia.trim() || null,
      region: region.trim(),
    }

    setGuardando(true)
    try {
      const actualizado = await modulosApi.actualizarPerfil(datos)
      setPerfil(actualizado)
      setEditando(false)
      setAviso('Tus cambios quedaron guardados.')
    } catch (fallo: unknown) {
      if (fallo instanceof ErrorApi && fallo.estado === 401) {
        setErrorFormulario('Tu sesión venció. Vuelve a ingresar para guardar los cambios.')
      } else if (fallo instanceof ErrorApi && fallo.estado === 403) {
        setErrorFormulario('Tu cuenta no puede editar este perfil.')
      } else {
        setErrorFormulario(mensajeDeFallo(fallo, 'No pudimos guardar los cambios. Revisa tu conexión.'))
      }
    } finally {
      setGuardando(false)
    }
  }

  const enlacePortafolio = perfil ? enlaceExterno(perfil.portafolio_url) : null

  return (
    <Disposicion>
      <div className="mx-auto max-w-2xl px-4 py-12">
        <header>
          <h1 className="text-3xl font-black tracking-tight text-tinta-900">Mi perfil</h1>
          <p className="mt-3 text-base text-tinta-600">
            Lo que muestra la comunidad sobre ti: tu especialidad, tu región y
            dónde ver tus trabajos.
          </p>
        </header>

        {cargandoAuth && (
          <p aria-live="polite" className="mt-8 text-sm text-tinta-600">
            Revisando tu sesión…
          </p>
        )}

        {!cargandoAuth && !usuario && (
          <Tarjeta className="mt-8">
            <h2 className="text-lg font-bold text-tinta-900">Necesitas ingresar</h2>
            <p className="mt-2 text-sm leading-relaxed text-tinta-600">
              Tu perfil es personal. Inicia sesión para verlo y editarlo; si
              todavía no tienes cuenta, puedes crear una en un minuto.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                to="/ingresar"
                state={{ desde: '/perfil' }}
                className="inline-flex items-center rounded-control bg-marca-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-marca-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
              >
                Ingresar
              </Link>
              <Link
                to="/registro"
                className="inline-flex items-center rounded-control border border-tinta-300 bg-white px-4 py-2.5 text-sm font-semibold text-tinta-900 hover:bg-tinta-100"
              >
                Crear cuenta
              </Link>
            </div>
          </Tarjeta>
        )}

        {usuario && cargando && (
          <p aria-live="polite" className="mt-8 text-sm text-tinta-600">
            {perfil ? 'Actualizando tu perfil…' : 'Cargando tu perfil…'}
          </p>
        )}

        {usuario && error && (
          <div role="alert" className="mt-8 rounded-control bg-error-50 px-4 py-4 text-sm text-error-600">
            <p className="font-medium">{error}</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Boton variante="secundario" tamano="sm" onClick={() => setReintento((valor) => valor + 1)}>
                Reintentar
              </Boton>
              <Link to="/ingresar" className="text-sm font-semibold text-error-600 hover:underline">
                Volver a ingresar
              </Link>
            </div>
          </div>
        )}

        {/* Un error de recarga no borra el perfil ya cargado. */}
        {usuario && perfil && (
          <>
            {aviso && (
              <p
                role="status"
                className="mt-6 rounded-control border border-tinta-200 bg-white px-3 py-2 text-sm font-medium text-exito-600"
              >
                {aviso}
              </p>
            )}

            {!editando ? (
              <Tarjeta className="mt-6">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-2xl font-bold text-tinta-900">{perfil.nombre}</h2>
                    <p className="mt-1 text-sm text-tinta-500">{perfil.rol}</p>
                  </div>
                  <Boton variante="secundario" onClick={abrirEdicion}>
                    Editar perfil
                  </Boton>
                </div>

                <dl className="mt-6 space-y-4 text-sm">
                  <div>
                    <dt className="font-semibold text-tinta-800">Región</dt>
                    <dd className="mt-1 text-tinta-600">{perfil.region || 'No informada'}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-tinta-800">Especialidad</dt>
                    <dd className="mt-1 text-tinta-600">
                      {perfil.especialidad || 'Todavía no la cuentas. ¡Agrega algo sobre lo que haces!'}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-tinta-800">Portafolio</dt>
                    <dd className="mt-1">
                      {enlacePortafolio ? (
                        <a
                          href={enlacePortafolio}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-semibold text-marca-700 hover:underline"
                        >
                          Ver mis trabajos <span aria-hidden="true">↗</span>
                        </a>
                      ) : (
                        <span className="text-tinta-600">Sin enlace todavía</span>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-tinta-800">Biografía</dt>
                    <dd className="mt-1 whitespace-pre-wrap leading-relaxed text-tinta-600">
                      {perfil.biografia || 'Aún no escribes una biografía.'}
                    </dd>
                  </div>
                </dl>
              </Tarjeta>
            ) : (
              <Tarjeta className="mt-6">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-lg font-bold text-tinta-900">Editar mi perfil</h2>
                  <Etiqueta tono="marca">{perfil.nombre}</Etiqueta>
                </div>

                <form onSubmit={guardar} className="mt-5 flex flex-col gap-4" noValidate>
                  <Campo
                    etiqueta="Especialidad"
                    id="perfil-especialidad"
                    ayuda="Por ejemplo: armaduras de EVA, pelucas, maquillaje de caracterización."
                    maxLength={120}
                    value={especialidad}
                    onChange={(evento) => setEspecialidad(evento.target.value)}
                  />

                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="perfil-region" className="text-sm font-medium text-tinta-800">
                      Región
                    </label>
                    <select
                      id="perfil-region"
                      value={region}
                      onChange={(evento) => setRegion(evento.target.value)}
                      className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                    >
                      <option value="">Prefiero no indicarla</option>
                      {REGIONES_CHILE.map((nombre) => (
                        <option key={nombre} value={nombre}>
                          {nombre}
                        </option>
                      ))}
                      {region && !REGIONES_CHILE.includes(region) && (
                        <option value={region}>{region}</option>
                      )}
                    </select>
                  </div>

                  <Campo
                    etiqueta="URL del portafolio"
                    id="perfil-portafolio"
                    type="url"
                    placeholder="https://…"
                    maxLength={500}
                    value={portafolioUrl}
                    onChange={(evento) => setPortafolioUrl(evento.target.value)}
                  />

                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="perfil-biografia" className="text-sm font-medium text-tinta-800">
                      Biografía
                    </label>
                    <textarea
                      id="perfil-biografia"
                      rows={5}
                      maxLength={2000}
                      value={biografia}
                      onChange={(evento) => setBiografia(evento.target.value)}
                      placeholder="Cuéntale a la comunidad desde cuándo haces cosplay y qué te gusta construir."
                      className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 placeholder:text-tinta-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                    />
                  </div>

                  {errorFormulario && (
                    <p role="alert" className="rounded-control bg-error-50 px-3 py-2 text-sm font-medium text-error-600">
                      {errorFormulario}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-3">
                    <Boton type="submit" cargando={guardando}>
                      Guardar cambios
                    </Boton>
                    <Boton
                      type="button"
                      variante="secundario"
                      onClick={() => {
                        setEditando(false)
                        setErrorFormulario('')
                      }}
                      disabled={guardando}
                    >
                      Cancelar
                    </Boton>
                  </div>
                </form>
              </Tarjeta>
            )}
          </>
        )}
      </div>
    </Disposicion>
  )
}
