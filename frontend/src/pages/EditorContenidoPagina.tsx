import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Campo } from '../components/ui/Campo'
import { api, ErrorApi, type Categoria, type Contenido, type TipoContenido } from '../lib/api'
import { useAuth } from '../lib/contextoAuth'
import { ETIQUETAS_CONTENIDO } from '../lib/contenido'
import { useEffect } from 'react'

/** Convierte un textarea en lista: una entrada por línea, sin vacías. */
function lineas(texto: string): string[] {
  return texto
    .split('\n')
    .map((linea) => linea.trim())
    .filter(Boolean)
}

/** Convierte "pecho: 98 cm" por línea en pares parte/valor. */
function medidas(texto: string): { parte: string; valor: string }[] {
  return lineas(texto)
    .map((linea) => {
      const separador = linea.indexOf(':')
      if (separador === -1) return null
      const parte = linea.slice(0, separador).trim()
      const valor = linea.slice(separador + 1).trim()
      return parte && valor ? { parte, valor } : null
    })
    .filter((par): par is { parte: string; valor: string } => par !== null)
}

const TIPOS: TipoContenido[] = ['guia', 'entrevista', 'articulo']

export function EditorContenidoPagina() {
  const { usuario, cargando } = useAuth()
  const navegar = useNavigate()

  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [tipo, setTipo] = useState<TipoContenido>('guia')
  const [titulo, setTitulo] = useState('')
  const [resumen, setResumen] = useState('')
  const [nivel, setNivel] = useState('basico')
  const [idCategoria, setIdCategoria] = useState('')
  const [cuerpo, setCuerpo] = useState('')
  const [videoUrl, setVideoUrl] = useState('')

  const [personaje, setPersonaje] = useState('')
  const [medidasTexto, setMedidasTexto] = useState('')
  const [tecnicas, setTecnicas] = useState('')
  const [presupuesto, setPresupuesto] = useState('')
  const [seguridad, setSeguridad] = useState('')
  const [pasos, setPasos] = useState('')
  const [materiales, setMateriales] = useState('')

  const [preguntas, setPreguntas] = useState('')
  const [respuestas, setRespuestas] = useState('')
  const [enlaces, setEnlaces] = useState('')

  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [creado, setCreado] = useState<Contenido | null>(null)
  const [publicando, setPublicando] = useState(false)

  useEffect(() => {
    let vigente = true
    api
      .categorias()
      .then((datos) => {
        if (vigente) setCategorias(datos)
      })
      .catch(() => {
        // Sin categorías el formulario sigue funcionando: la categoría es opcional.
      })
    return () => {
      vigente = false
    }
  }, [])

  if (cargando) {
    return (
      <Disposicion>
        <p className="mx-auto max-w-2xl px-4 py-16 text-sm text-tinta-500">Cargando…</p>
      </Disposicion>
    )
  }

  if (!usuario) {
    return <Navigate to="/ingresar" state={{ desde: '/contenido/nuevo' }} replace />
  }

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    setError('')
    setEnviando(true)

    const comunes = {
      tipo,
      titulo: titulo.trim(),
      resumen: resumen.trim() || null,
      nivel,
      id_categoria: idCategoria || null,
      cuerpo: cuerpo.trim() || null,
      video_url: videoUrl.trim() || null,
    }

    const especificos =
      tipo === 'guia'
        ? {
            personaje: personaje.trim() || null,
            medidas: medidas(medidasTexto),
            tecnicas: lineas(tecnicas),
            presupuesto: presupuesto.trim() || null,
            seguridad: seguridad.trim() || null,
            pasos: lineas(pasos),
            materiales: lineas(materiales),
          }
        : tipo === 'entrevista'
          ? { preguntas: lineas(preguntas), respuestas: lineas(respuestas) }
          : { enlaces: lineas(enlaces) }

    try {
      const contenido = await api.crearContenido({ ...comunes, ...especificos })
      setCreado(contenido)
    } catch (fallo) {
      if (fallo instanceof ErrorApi) setError(fallo.message)
      else setError('No pudimos guardar el contenido. Revisa tu conexión.')
    } finally {
      setEnviando(false)
    }
  }

  async function publicar() {
    if (!creado) return
    setPublicando(true)
    setError('')
    try {
      await api.publicarContenido(creado.id_contenido)
      navegar(`/contenido/${creado.id_contenido}`)
    } catch (fallo) {
      if (fallo instanceof ErrorApi) setError(fallo.message)
      else setError('No pudimos publicar el contenido.')
    } finally {
      setPublicando(false)
    }
  }

  // --- Pantalla de confirmación tras guardar ---------------------------
  if (creado) {
    return (
      <Disposicion>
        <div className="mx-auto max-w-lg px-4 py-20 text-center">
          <h1 className="text-2xl font-bold text-tinta-900">Borrador guardado</h1>
          <p className="mt-3 text-sm leading-relaxed text-tinta-600">
            «{creado.titulo}» quedó como borrador. No aparece en el listado público
            hasta que un administrador lo publique.
          </p>

          {error && (
            <p role="alert" className="mt-6 rounded-control bg-error-50 px-3 py-2 text-sm text-error-600">
              {error}
            </p>
          )}

          <div className="mt-8 flex flex-col items-center gap-3">
            {usuario.rol === 'administrador' ? (
              <Boton onClick={publicar} cargando={publicando} tamano="lg">
                {publicando ? 'Publicando' : 'Publicar ahora'}
              </Boton>
            ) : (
              <p className="text-xs text-tinta-500">
                Un administrador tiene que revisarlo antes de que se publique.
              </p>
            )}
            <Boton variante="secundario" onClick={() => navegar('/contenido')}>
              Ir a contenidos
            </Boton>
          </div>
        </div>
      </Disposicion>
    )
  }

  // --- Formulario -----------------------------------------------------
  return (
    <Disposicion>
      <div className="mx-auto max-w-2xl px-4 py-12">
        <h1 className="text-2xl font-bold tracking-tight text-tinta-900">
          Nuevo contenido
        </h1>
        <p className="mt-2 text-sm text-tinta-600">
          Elige el tipo y el formulario cambia. Cada tipo tiene sus propios campos.
        </p>

        <form onSubmit={enviar} className="mt-8 flex flex-col gap-5" noValidate>
          <fieldset>
            <legend className="text-sm font-medium text-tinta-800">Tipo de contenido</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {TIPOS.map((valor) => (
                <label
                  key={valor}
                  className={[
                    'cursor-pointer rounded-control border px-4 py-2 text-sm font-medium',
                    tipo === valor
                      ? 'border-marca-600 bg-marca-50 text-marca-800'
                      : 'border-tinta-300 bg-white text-tinta-700 hover:bg-tinta-100',
                  ].join(' ')}
                >
                  <input
                    type="radio"
                    name="tipo"
                    value={valor}
                    checked={tipo === valor}
                    onChange={() => setTipo(valor)}
                    className="sr-only"
                  />
                  {ETIQUETAS_CONTENIDO[valor]}
                </label>
              ))}
            </div>
          </fieldset>

          <Campo
            etiqueta="Título"
            id="titulo"
            required
            minLength={3}
            value={titulo}
            onChange={(evento) => setTitulo(evento.target.value)}
          />

          <Campo
            etiqueta="Resumen"
            id="resumen"
            ayuda="Una o dos frases. Es lo que se ve en el listado."
            value={resumen}
            onChange={(evento) => setResumen(evento.target.value)}
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="nivel" className="text-sm font-medium text-tinta-800">
                Nivel
              </label>
              <select
                id="nivel"
                value={nivel}
                onChange={(evento) => setNivel(evento.target.value)}
                className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
              >
                <option value="basico">Básico</option>
                <option value="intermedio">Intermedio</option>
                <option value="avanzado">Avanzado</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="categoria" className="text-sm font-medium text-tinta-800">
                Categoría
              </label>
              <select
                id="categoria"
                value={idCategoria}
                onChange={(evento) => setIdCategoria(evento.target.value)}
                className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
              >
                <option value="">Sin categoría</option>
                {categorias.map((categoria) => (
                  <option key={categoria.id_categoria} value={categoria.id_categoria}>
                    {categoria.nombre}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="cuerpo" className="text-sm font-medium text-tinta-800">
              Cuerpo
            </label>
            <textarea
              id="cuerpo"
              rows={8}
              value={cuerpo}
              onChange={(evento) => setCuerpo(evento.target.value)}
              placeholder="<p>Puedes usar HTML simple: párrafos, negritas, listas y enlaces.</p>"
              className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 font-mono text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
            />
            <p className="text-xs text-tinta-500">
              Se muestra sanitizado en la vista pública.
            </p>
          </div>

          <Campo
            etiqueta="URL del video (opcional)"
            id="video"
            ayuda="Solo YouTube, Vimeo o TikTok."
            value={videoUrl}
            onChange={(evento) => setVideoUrl(evento.target.value)}
          />

          {tipo === 'guia' && (
            <>
              <hr className="border-tinta-200" />
              <p className="text-xs font-semibold uppercase tracking-wide text-tinta-500">
                Campos de la guía
              </p>

              <Campo
                etiqueta="Personaje"
                id="personaje"
                value={personaje}
                onChange={(evento) => setPersonaje(evento.target.value)}
              />

              <div className="flex flex-col gap-1.5">
                <label htmlFor="medidas" className="text-sm font-medium text-tinta-800">
                  Medidas
                </label>
                <textarea
                  id="medidas"
                  rows={3}
                  value={medidasTexto}
                  onChange={(evento) => setMedidasTexto(evento.target.value)}
                  placeholder={'pecho: 98 cm\nalto: 1,72 m'}
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 font-mono text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                />
                <p className="text-xs text-tinta-500">Una por línea, con el formato «parte: valor».</p>
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="tecnicas" className="text-sm font-medium text-tinta-800">
                  Técnicas
                </label>
                <textarea
                  id="tecnicas"
                  rows={3}
                  value={tecnicas}
                  onChange={(evento) => setTecnicas(evento.target.value)}
                  placeholder="termoformado&#10;sellado de bordes"
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                />
                <p className="text-xs text-tinta-500">Una por línea.</p>
              </div>

              <Campo
                etiqueta="Presupuesto declarado"
                id="presupuesto"
                ayuda="Rango estimado, por ejemplo «$45.000 a $60.000 CLP»."
                value={presupuesto}
                onChange={(evento) => setPresupuesto(evento.target.value)}
              />

              <div className="flex flex-col gap-1.5">
                <label htmlFor="seguridad" className="text-sm font-medium text-tinta-800">
                  Seguridad
                </label>
                <textarea
                  id="seguridad"
                  rows={3}
                  value={seguridad}
                  onChange={(evento) => setSeguridad(evento.target.value)}
                  placeholder="Ventilación, protección respiratoria, manejo de herramientas."
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="pasos" className="text-sm font-medium text-tinta-800">
                  Pasos
                </label>
                <textarea
                  id="pasos"
                  rows={4}
                  value={pasos}
                  onChange={(evento) => setPasos(evento.target.value)}
                  placeholder="Trazo&#10;Corte&#10;Termoformado"
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                />
                <p className="text-xs text-tinta-500">Uno por línea, en orden.</p>
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="materiales" className="text-sm font-medium text-tinta-800">
                  Materiales
                </label>
                <textarea
                  id="materiales"
                  rows={3}
                  value={materiales}
                  onChange={(evento) => setMateriales(evento.target.value)}
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                />
                <p className="text-xs text-tinta-500">Uno por línea.</p>
              </div>
            </>
          )}

          {tipo === 'entrevista' && (
            <>
              <hr className="border-tinta-200" />
              <p className="text-xs font-semibold uppercase tracking-wide text-tinta-500">
                Campos de la entrevista
              </p>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="preguntas" className="text-sm font-medium text-tinta-800">
                  Preguntas
                </label>
                <textarea
                  id="preguntas"
                  rows={4}
                  value={preguntas}
                  onChange={(evento) => setPreguntas(evento.target.value)}
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                />
                <p className="text-xs text-tinta-500">Una por línea.</p>
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="respuestas" className="text-sm font-medium text-tinta-800">
                  Respuestas
                </label>
                <textarea
                  id="respuestas"
                  rows={4}
                  value={respuestas}
                  onChange={(evento) => setRespuestas(evento.target.value)}
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                />
                <p className="text-xs text-tinta-500">
                  Una por línea. Se emparejan con las preguntas en el mismo orden.
                </p>
              </div>
            </>
          )}

          {tipo === 'articulo' && (
            <>
              <hr className="border-tinta-200" />
              <p className="text-xs font-semibold uppercase tracking-wide text-tinta-500">
                Campos del artículo
              </p>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="enlaces" className="text-sm font-medium text-tinta-800">
                  Enlaces
                </label>
                <textarea
                  id="enlaces"
                  rows={4}
                  value={enlaces}
                  onChange={(evento) => setEnlaces(evento.target.value)}
                  placeholder="https://ejemplo.cl/tiendas"
                  className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 font-mono text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
                />
                <p className="text-xs text-tinta-500">Una URL por línea.</p>
              </div>
            </>
          )}

          {error && (
            <p role="alert" className="rounded-control bg-error-50 px-3 py-2 text-sm font-medium text-error-600">
              {error}
            </p>
          )}

          <Boton type="submit" cargando={enviando} tamano="lg">
            {enviando ? 'Guardando' : 'Guardar como borrador'}
          </Boton>
        </form>
      </div>
    </Disposicion>
  )
}
