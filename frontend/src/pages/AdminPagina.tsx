import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate } from 'react-router-dom'

import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import { Campo } from '../components/ui/Campo'
import { Etiqueta } from '../components/ui/Etiqueta'
import { Tarjeta } from '../components/ui/Tarjeta'
import {
  adminApi,
  cargarPanel,
  fechaLocalAISO,
  mesActual,
  type DatosPanel,
  type EstadoTema,
  type ResumenAdmin,
} from '../lib/admin'
import { useAuth } from '../lib/contextoAuth'
import {
  ETIQUETAS_PLATAFORMA,
  ETIQUETAS_TIPO_EVENTO,
  ETIQUETAS_TIPO_TIENDA,
  PLATAFORMAS,
  REGIONES_CHILE,
  TIPOS_EVENTO,
  TIPOS_TIENDA,
  formatearFecha,
  formatearFechaHora,
  formatearMes,
  mensajeDeFallo,
  type Evento,
  type Grupo,
  type Tienda,
} from '../lib/modulos'

type Seccion =
  | 'resumen'
  | 'contenido'
  | 'eventos'
  | 'foro'
  | 'desafios'
  | 'usuarios'
  | 'comunidad'

const SECCIONES: { clave: Seccion; nombre: string }[] = [
  { clave: 'resumen', nombre: 'Resumen' },
  { clave: 'contenido', nombre: 'Contenido' },
  { clave: 'eventos', nombre: 'Eventos' },
  { clave: 'foro', nombre: 'Foro' },
  { clave: 'desafios', nombre: 'Desafíos' },
  { clave: 'usuarios', nombre: 'Usuarios' },
  { clave: 'comunidad', nombre: 'Comunidad' },
]

const METRICAS: { clave: keyof ResumenAdmin; nombre: string }[] = [
  { clave: 'usuarios', nombre: 'Cuentas' },
  { clave: 'contenido_publicado', nombre: 'Publicados' },
  { clave: 'contenido_pendiente', nombre: 'Borradores' },
  { clave: 'eventos', nombre: 'Eventos' },
  { clave: 'inscripciones', nombre: 'Inscripciones' },
  { clave: 'temas', nombre: 'Temas del foro' },
  { clave: 'respuestas', nombre: 'Respuestas' },
  { clave: 'desafios', nombre: 'Desafíos' },
  { clave: 'tiendas', nombre: 'Tiendas' },
  { clave: 'grupos', nombre: 'Grupos' },
  { clave: 'proveedores', nombre: 'Profesionales' },
  { clave: 'categorias', nombre: 'Categorías' },
]

interface Formulario {
  eventoTitulo: string
  eventoTipo: Evento['tipo']
  eventoFecha: string
  eventoLugar: string
  eventoRegion: string
  desafioTitulo: string
  desafioMes: string
  desafioId: string
  ganadorId: string
  tiendaNombre: string
  tiendaTipo: Tienda['tipo']
  tiendaRegion: string
  tiendaEnlace: string
  grupoTitulo: string
  grupoPlataforma: Grupo['plataforma']
  grupoRegion: string
  grupoEnlace: string
  categoriaNombre: string
}

const FORMULARIO_INICIAL: Formulario = {
  eventoTitulo: '',
  eventoTipo: 'convencion',
  eventoFecha: '',
  eventoLugar: '',
  eventoRegion: '',
  desafioTitulo: '',
  desafioMes: mesActual(),
  desafioId: '',
  ganadorId: '',
  tiendaNombre: '',
  tiendaTipo: 'insumos',
  tiendaRegion: '',
  tiendaEnlace: '',
  grupoTitulo: '',
  grupoPlataforma: 'discord',
  grupoRegion: '',
  grupoEnlace: '',
  categoriaNombre: '',
}

interface Opcion {
  valor: string
  texto: string
}

/** Select con la misma apariencia y etiqueta asociada que `Campo`. */
function Selector({
  etiqueta,
  id,
  valor,
  opciones,
  onChange,
}: {
  etiqueta: string
  id: string
  valor: string
  opciones: Opcion[]
  onChange: (valor: string) => void
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-tinta-800">
        {etiqueta}
      </label>
      <select
        id={id}
        value={valor}
        onChange={(evento) => onChange(evento.target.value)}
        className="rounded-control border border-tinta-300 bg-white px-3 py-2.5 text-sm text-tinta-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marca-600"
      >
        {opciones.map((opcion) => (
          <option key={opcion.valor} value={opcion.valor}>
            {opcion.texto}
          </option>
        ))}
      </select>
    </div>
  )
}

const CLASES_TABLA =
  'w-full min-w-[36rem] border-collapse text-left text-sm'
const CLASES_CELDA = 'border-b border-tinta-200 px-3 py-2.5 align-top'
const CLASES_CABECERA =
  'border-b border-tinta-300 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-tinta-500'

function Tabla({ encabezados, children }: { encabezados: string[]; children: ReactNode }) {
  return (
    <div className="mt-4 overflow-x-auto">
      <table className={CLASES_TABLA}>
        <thead>
          <tr>
            {encabezados.map((texto) => (
              <th key={texto} scope="col" className={CLASES_CABECERA}>
                {texto}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}

/**
 * Panel de administración. Solo entra quien tenga rol `administrador`; el
 * backend vuelve a validar el rol en cada petición, así que esta guarda es
 * comodidad de interfaz, no el control de acceso.
 */
export function AdminPagina() {
  const { usuario, cargando: validandoSesion } = useAuth()

  const [seccion, setSeccion] = useState<Seccion>('resumen')
  const [datos, setDatos] = useState<DatosPanel | null>(null)
  const [cargando, setCargando] = useState(true)
  const [errorCarga, setErrorCarga] = useState('')
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [accion, setAccion] = useState('')
  const [recarga, setRecarga] = useState(0)
  const [form, setForm] = useState<Formulario>(FORMULARIO_INICIAL)
  const [pendienteBorrar, setPendienteBorrar] = useState<string | null>(null)

  useEffect(() => {
    if (!usuario || usuario.rol !== 'administrador') return
    let vigente = true
    // El reinicio va en microtarea: un setState sincrónico dentro del effect
    // provoca un render en cascada (regla de React Compiler).
    queueMicrotask(() => {
      if (!vigente) return
      setCargando(true)
      setErrorCarga('')
      cargarPanel()
        .then((resultado) => {
          if (!vigente) return
          setDatos(resultado)
          setCargando(false)
        })
        .catch((fallo: unknown) => {
          if (!vigente) return
          setErrorCarga(mensajeDeFallo(fallo, 'No pudimos cargar el panel.'))
          setCargando(false)
        })
    })
    return () => {
      vigente = false
    }
  }, [recarga, usuario])

  function cambiar<K extends keyof Formulario>(clave: K, valor: Formulario[K]) {
    setForm((anterior) => ({ ...anterior, [clave]: valor }))
  }

  /** Devuelve true si la acción salió bien, para poder limpiar el formulario. */
  async function ejecutar(
    clave: string,
    tarea: () => Promise<unknown>,
    exito: string,
  ): Promise<boolean> {
    setAccion(clave)
    setAviso('')
    setError('')
    try {
      await tarea()
      setAviso(exito)
      setRecarga((valor) => valor + 1)
      return true
    } catch (fallo: unknown) {
      setError(mensajeDeFallo(fallo, 'No se pudo completar la acción.'))
      return false
    } finally {
      setAccion('')
    }
  }

  const ocupado = (clave: string) => accion === clave

  // --- Guardas de acceso --------------------------------------------------

  if (validandoSesion) {
    return (
      <Disposicion>
        <div className="mx-auto max-w-6xl px-4 py-16">
          <p className="text-sm text-tinta-600">Verificando sesión…</p>
        </div>
      </Disposicion>
    )
  }

  if (!usuario) {
    return <Navigate to="/ingresar" replace state={{ desde: '/admin' }} />
  }

  if (usuario.rol !== 'administrador') {
    return (
      <Disposicion>
        <div className="mx-auto max-w-2xl px-4 py-16">
          <h1 className="text-2xl font-bold text-tinta-900">Acceso restringido</h1>
          <p className="mt-3 text-sm text-tinta-600">
            El panel es solo para administradores. Tu cuenta tiene el rol{' '}
            <strong className="font-semibold text-tinta-900">{usuario.rol}</strong>.
          </p>
          <Link
            to="/"
            className="mt-6 inline-block rounded-control bg-marca-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-marca-800"
          >
            Volver al inicio
          </Link>
        </div>
      </Disposicion>
    )
  }

  // --- Acciones -----------------------------------------------------------

  async function enviarEvento(evento: FormEvent) {
    evento.preventDefault()
    const fecha = fechaLocalAISO(form.eventoFecha)
    if (!fecha) {
      setError('Indica una fecha y hora válidas para el evento.')
      return
    }
    const ok = await ejecutar(
      'crear-evento',
      () =>
        adminApi.crearEvento({
          nombre: form.eventoTitulo.trim(),
          tipo: form.eventoTipo,
          fecha_inicio: fecha,
          lugar: form.eventoLugar.trim(),
          region: form.eventoRegion || null,
        }),
      'Evento creado y publicado en el calendario.',
    )
    if (ok) {
      setForm((anterior) => ({
        ...anterior,
        eventoTitulo: '',
        eventoFecha: '',
        eventoLugar: '',
      }))
    }
  }

  async function enviarDesafio(evento: FormEvent) {
    evento.preventDefault()
    const ok = await ejecutar(
      'crear-desafio',
      () =>
        adminApi.crearDesafio({
          titulo: form.desafioTitulo.trim(),
          mes: form.desafioMes,
        }),
      'Desafío creado.',
    )
    if (ok) setForm((anterior) => ({ ...anterior, desafioTitulo: '' }))
  }

  async function enviarGanador(evento: FormEvent) {
    evento.preventDefault()
    if (!form.desafioId || !form.ganadorId) return
    await ejecutar(
      'asignar-ganador',
      () => adminApi.asignarGanador(form.desafioId, form.ganadorId),
      'Ganador asignado.',
    )
  }

  async function enviarTienda(evento: FormEvent) {
    evento.preventDefault()
    const ok = await ejecutar(
      'crear-tienda',
      () =>
        adminApi.crearTienda({
          nombre: form.tiendaNombre.trim(),
          tipo: form.tiendaTipo,
          envia_a_chile: true,
          enlace_web: form.tiendaEnlace.trim() || null,
          region: form.tiendaRegion || null,
        }),
      'Tienda agregada al directorio.',
    )
    if (ok) {
      setForm((anterior) => ({
        ...anterior,
        tiendaNombre: '',
        tiendaEnlace: '',
      }))
    }
  }

  async function enviarGrupo(evento: FormEvent) {
    evento.preventDefault()
    const ok = await ejecutar(
      'crear-grupo',
      () =>
        adminApi.crearGrupo({
          nombre: form.grupoTitulo.trim(),
          plataforma: form.grupoPlataforma,
          region: form.grupoRegion || null,
          enlace: form.grupoEnlace.trim() || null,
        }),
      'Grupo agregado a la comunidad.',
    )
    if (ok) {
      setForm((anterior) => ({
        ...anterior,
        grupoTitulo: '',
        grupoEnlace: '',
      }))
    }
  }

  async function enviarCategoria(evento: FormEvent) {
    evento.preventDefault()
    const ok = await ejecutar(
      'crear-categoria',
      () => adminApi.crearCategoria(form.categoriaNombre.trim()),
      'Categoría creada.',
    )
    if (ok) setForm((anterior) => ({ ...anterior, categoriaNombre: '' }))
  }

  // --- Render -------------------------------------------------------------

  const opcionesUsuarios: Opcion[] = (datos?.usuarios.elementos ?? []).map((u) => ({
    valor: u.id_usuario,
    texto: `${u.nombre} · ${u.correo}`,
  }))
  const opcionesDesafios: Opcion[] = (datos?.desafios.elementos ?? []).map((d) => ({
    valor: d.id_desafio,
    texto: `${formatearMes(d.mes)} · ${d.titulo}`,
  }))
  const opcionesRegiones: Opcion[] = [
    { valor: '', texto: 'Sin región' },
    ...REGIONES_CHILE.map((region) => ({ valor: region, texto: region })),
  ]

  return (
    <Disposicion>
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-marca-700">
              Administración
            </p>
            <h1 className="mt-1 text-3xl font-black tracking-tight text-tinta-900">
              Panel de gestión
            </h1>
            <p className="mt-2 text-sm text-tinta-600">
              Sesión de <strong className="font-semibold text-tinta-900">{usuario.nombre}</strong>{' '}
              · modera contenido, organiza eventos y administra la comunidad.
            </p>
          </div>
          <Boton
            variante="secundario"
            tamano="sm"
            onClick={() => setRecarga((valor) => valor + 1)}
            cargando={cargando}
          >
            Actualizar
          </Boton>
        </header>

        <p aria-live="polite" className="mt-6 text-sm text-tinta-600">
          {cargando ? (datos ? 'Actualizando datos…' : 'Cargando panel…') : ''}
        </p>

        {errorCarga && (
          <div role="alert" className="mt-4 rounded-control bg-error-50 px-3 py-3 text-sm text-error-600">
            <p className="font-medium">{errorCarga}</p>
            <Boton
              variante="secundario"
              tamano="sm"
              className="mt-3"
              onClick={() => setRecarga((valor) => valor + 1)}
            >
              Reintentar
            </Boton>
          </div>
        )}

        {aviso && (
          <p role="status" className="mt-4 rounded-control bg-exito-100 px-3 py-2.5 text-sm font-medium text-exito-600">
            {aviso}
          </p>
        )}
        {error && (
          <p role="alert" className="mt-4 rounded-control bg-error-50 px-3 py-2.5 text-sm font-medium text-error-600">
            {error}
          </p>
        )}

        <div role="tablist" aria-label="Secciones del panel" className="mt-8 flex flex-wrap gap-2 border-b border-tinta-200 pb-3">
          {SECCIONES.map((item) => (
            <button
              key={item.clave}
              type="button"
              role="tab"
              aria-selected={seccion === item.clave}
              onClick={() => setSeccion(item.clave)}
              className={[
                'rounded-control px-3 py-2 text-sm font-semibold',
                seccion === item.clave
                  ? 'bg-marca-700 text-white'
                  : 'bg-white text-tinta-700 hover:bg-tinta-100',
              ].join(' ')}
            >
              {item.nombre}
            </button>
          ))}
        </div>

        {datos && (
          <div role="tabpanel" className="mt-8">
            {/* ------------------------------ Resumen ------------------------------ */}
            {seccion === 'resumen' && (
              <section aria-labelledby="titulo-resumen">
                <h2 id="titulo-resumen" className="text-xl font-bold text-tinta-900">
                  Estado de la plataforma
                </h2>
                <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {METRICAS.map((metrica) => (
                    <Tarjeta key={metrica.clave} className="p-5">
                      <p className="text-xs font-semibold uppercase tracking-wide text-tinta-500">
                        {metrica.nombre}
                      </p>
                      <p className="mt-2 text-3xl font-black text-marca-800">
                        {String(datos.resumen[metrica.clave])}
                      </p>
                    </Tarjeta>
                  ))}
                </div>
                <p className="mt-5 text-xs text-tinta-500">
                  {datos.resumen.usuarios_activos} de {datos.resumen.usuarios} cuentas activas ·{' '}
                  {datos.resumen.contenido_rechazado} contenidos rechazados ·{' '}
                  {datos.resumen.temas_abiertos} temas abiertos.
                </p>
              </section>
            )}

            {/* ----------------------------- Contenido ---------------------------- */}
            {seccion === 'contenido' && (
              <section aria-labelledby="titulo-contenido">
                <h2 id="titulo-contenido" className="text-xl font-bold text-tinta-900">
                  Bandeja editorial
                </h2>
                <p className="mt-2 text-sm text-tinta-600">
                  Aquí se ven los borradores, que el sitio público no muestra hasta que se publican.
                </p>
                {datos.contenido.elementos.length === 0 ? (
                  <p className="mt-6 text-sm text-tinta-600">Todavía no hay contenidos.</p>
                ) : (
                  <Tabla encabezados={['Título', 'Tipo', 'Estado', 'Acciones']}>
                    {datos.contenido.elementos.map((item) => (
                      <tr key={item.id_contenido}>
                        <td className={CLASES_CELDA}>
                          <p className="font-semibold text-tinta-900">{item.titulo}</p>
                          <p className="mt-0.5 text-xs text-tinta-500">
                            {formatearFecha(item.creado_en)}
                          </p>
                        </td>
                        <td className={CLASES_CELDA}>{item.tipo}</td>
                        <td className={CLASES_CELDA}>
                          <Etiqueta
                            tono={
                              item.estado === 'publicado'
                                ? 'exito'
                                : item.estado === 'rechazado'
                                  ? 'acento'
                                  : 'neutro'
                            }
                          >
                            {item.estado}
                          </Etiqueta>
                        </td>
                        <td className={CLASES_CELDA}>
                          <div className="flex flex-wrap gap-2">
                            {item.estado !== 'publicado' && (
                              <Boton
                                variante="primario"
                                tamano="sm"
                                cargando={ocupado(`publicar-${item.id_contenido}`)}
                                onClick={() => {
                                  void ejecutar(
                                    `publicar-${item.id_contenido}`,
                                    () => adminApi.publicarContenido(item.id_contenido),
                                    'Contenido publicado.',
                                  )
                                }}
                              >
                                Publicar
                              </Boton>
                            )}
                            {item.estado === 'pendiente' && (
                              <Boton
                                variante="secundario"
                                tamano="sm"
                                cargando={ocupado(`rechazar-${item.id_contenido}`)}
                                onClick={() => {
                                  void ejecutar(
                                    `rechazar-${item.id_contenido}`,
                                    () => adminApi.rechazarContenido(item.id_contenido),
                                    'Borrador rechazado.',
                                  )
                                }}
                              >
                                Rechazar
                              </Boton>
                            )}
                            {item.estado !== 'pendiente' && (
                              <Boton
                                variante="fantasma"
                                tamano="sm"
                                cargando={ocupado(`borrador-${item.id_contenido}`)}
                                onClick={() => {
                                  void ejecutar(
                                    `borrador-${item.id_contenido}`,
                                    () => adminApi.volverABorrador(item.id_contenido),
                                    'Contenido devuelto a borrador.',
                                  )
                                }}
                              >
                                A borrador
                              </Boton>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </Tabla>
                )}

                <Tarjeta className="mt-8">
                  <h3 className="text-base font-bold text-tinta-900">Nueva categoría</h3>
                  <form onSubmit={(evento) => { void enviarCategoria(evento) }} className="mt-4 flex flex-wrap items-end gap-3">
                    <div className="min-w-56 flex-1">
                      <Campo
                        etiqueta="Nombre"
                        id="categoria-nombre"
                        required
                        minLength={2}
                        value={form.categoriaNombre}
                        onChange={(evento) => cambiar('categoriaNombre', evento.target.value)}
                      />
                    </div>
                    <Boton type="submit" cargando={ocupado('crear-categoria')}>
                      Crear
                    </Boton>
                  </form>
                  {datos.categorias.length > 0 && (
                    <p className="mt-3 text-xs text-tinta-500">
                      Existentes: {datos.categorias.map((c) => c.nombre).join(', ')}
                    </p>
                  )}
                </Tarjeta>
              </section>
            )}

            {/* ------------------------------ Eventos ----------------------------- */}
            {seccion === 'eventos' && (
              <section aria-labelledby="titulo-eventos">
                <h2 id="titulo-eventos" className="text-xl font-bold text-tinta-900">
                  Calendario de eventos
                </h2>
                <Tarjeta className="mt-5">
                  <h3 className="text-base font-bold text-tinta-900">Crear evento</h3>
                  <form onSubmit={(evento) => { void enviarEvento(evento) }} className="mt-4 grid gap-4 sm:grid-cols-2">
                    <Campo
                      etiqueta="Nombre del evento"
                      id="evento-titulo"
                      required
                      minLength={3}
                      value={form.eventoTitulo}
                      onChange={(evento) => cambiar('eventoTitulo', evento.target.value)}
                    />
                    <Selector
                      etiqueta="Tipo"
                      id="evento-tipo"
                      valor={form.eventoTipo}
                      opciones={TIPOS_EVENTO.map((tipo) => ({
                        valor: tipo,
                        texto: ETIQUETAS_TIPO_EVENTO[tipo],
                      }))}
                      onChange={(valor) => cambiar('eventoTipo', valor as Evento['tipo'])}
                    />
                    <Campo
                      etiqueta="Fecha y hora de inicio"
                      id="evento-fecha"
                      type="datetime-local"
                      required
                      value={form.eventoFecha}
                      onChange={(evento) => cambiar('eventoFecha', evento.target.value)}
                      ayuda="Se guarda en UTC; la web la muestra en hora de Chile."
                    />
                    <Campo
                      etiqueta="Lugar"
                      id="evento-lugar"
                      required
                      minLength={2}
                      value={form.eventoLugar}
                      onChange={(evento) => cambiar('eventoLugar', evento.target.value)}
                    />
                    <Selector
                      etiqueta="Región"
                      id="evento-region"
                      valor={form.eventoRegion}
                      opciones={opcionesRegiones}
                      onChange={(valor) => cambiar('eventoRegion', valor)}
                    />
                    <div className="sm:col-span-2">
                      <Boton type="submit" cargando={ocupado('crear-evento')}>
                        Publicar evento
                      </Boton>
                    </div>
                  </form>
                </Tarjeta>

                {datos.eventos.elementos.length === 0 ? (
                  <p className="mt-8 text-sm text-tinta-600">No hay eventos creados.</p>
                ) : (
                  <Tabla encabezados={['Evento', 'Fecha', 'Inscritos', 'Acciones']}>
                    {datos.eventos.elementos.map((item) => (
                      <tr key={item.id_evento}>
                        <td className={CLASES_CELDA}>
                          <p className="font-semibold text-tinta-900">{item.nombre}</p>
                          <p className="mt-0.5 text-xs text-tinta-500">
                            {ETIQUETAS_TIPO_EVENTO[item.tipo]} · {item.lugar}
                          </p>
                        </td>
                        <td className={CLASES_CELDA}>{formatearFechaHora(item.fecha_inicio)}</td>
                        <td className={CLASES_CELDA}>{item.total_participantes}</td>
                        <td className={CLASES_CELDA}>
                          {pendienteBorrar === item.id_evento ? (
                            <div className="flex flex-wrap gap-2">
                              <Boton
                                variante="primario"
                                tamano="sm"
                                cargando={ocupado(`borrar-${item.id_evento}`)}
                                onClick={() => {
                                  void ejecutar(
                                    `borrar-${item.id_evento}`,
                                    () => adminApi.eliminarEvento(item.id_evento),
                                    'Evento eliminado.',
                                  ).then(() => setPendienteBorrar(null))
                                }}
                              >
                                Confirmar
                              </Boton>
                              <Boton
                                variante="fantasma"
                                tamano="sm"
                                onClick={() => setPendienteBorrar(null)}
                              >
                                Cancelar
                              </Boton>
                            </div>
                          ) : (
                            <Boton
                              variante="secundario"
                              tamano="sm"
                              onClick={() => setPendienteBorrar(item.id_evento)}
                            >
                              Eliminar
                            </Boton>
                          )}
                        </td>
                      </tr>
                    ))}
                  </Tabla>
                )}
              </section>
            )}

            {/* ------------------------------- Foro ------------------------------- */}
            {seccion === 'foro' && (
              <section aria-labelledby="titulo-foro">
                <h2 id="titulo-foro" className="text-xl font-bold text-tinta-900">
                  Moderación del foro
                </h2>
                <p className="mt-2 text-sm text-tinta-600">
                  Un tema oculto desaparece del foro público pero sigue aquí para poder reabrirlo.
                </p>
                {datos.temas.elementos.length === 0 ? (
                  <p className="mt-6 text-sm text-tinta-600">Todavía no hay temas.</p>
                ) : (
                  <Tabla encabezados={['Tema', 'Autor', 'Estado', 'Acciones']}>
                    {datos.temas.elementos.map((tema) => (
                      <tr key={tema.id_tema}>
                        <td className={CLASES_CELDA}>
                          <p className="font-semibold text-tinta-900">{tema.titulo}</p>
                          <p className="mt-0.5 text-xs text-tinta-500">
                            {tema.categoria} · {tema.total_respuestas} respuestas
                          </p>
                        </td>
                        <td className={CLASES_CELDA}>{tema.nombre_autor}</td>
                        <td className={CLASES_CELDA}>
                          <Etiqueta tono={tema.estado === 'abierto' ? 'exito' : 'neutro'}>
                            {tema.estado}
                          </Etiqueta>
                        </td>
                        <td className={CLASES_CELDA}>
                          <div className="flex flex-wrap gap-2">
                            {(['abierto', 'cerrado', 'oculto'] as EstadoTema[]).map((estado) => (
                              <Boton
                                key={estado}
                                variante={tema.estado === estado ? 'fantasma' : 'secundario'}
                                tamano="sm"
                                disabled={tema.estado === estado}
                                cargando={ocupado(`tema-${tema.id_tema}-${estado}`)}
                                onClick={() => {
                                  void ejecutar(
                                    `tema-${tema.id_tema}-${estado}`,
                                    () => adminApi.cambiarEstadoTema(tema.id_tema, estado),
                                    `Tema marcado como ${estado}.`,
                                  )
                                }}
                              >
                                {estado === 'abierto' ? 'Reabrir' : estado === 'cerrado' ? 'Cerrar' : 'Ocultar'}
                              </Boton>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </Tabla>
                )}
              </section>
            )}

            {/* ----------------------------- Desafíos ----------------------------- */}
            {seccion === 'desafios' && (
              <section aria-labelledby="titulo-desafios">
                <h2 id="titulo-desafios" className="text-xl font-bold text-tinta-900">
                  Desafíos mensuales
                </h2>
                <div className="mt-5 grid gap-5 lg:grid-cols-2">
                  <Tarjeta>
                    <h3 className="text-base font-bold text-tinta-900">Nuevo desafío</h3>
                    <form onSubmit={(evento) => { void enviarDesafio(evento) }} className="mt-4 flex flex-col gap-4">
                      <Campo
                        etiqueta="Título"
                        id="desafio-titulo"
                        required
                        minLength={3}
                        value={form.desafioTitulo}
                        onChange={(evento) => cambiar('desafioTitulo', evento.target.value)}
                      />
                      <Campo
                        etiqueta="Mes (AAAA-MM)"
                        id="desafio-mes"
                        required
                        pattern="\d{4}-(0[1-9]|1[0-2])"
                        value={form.desafioMes}
                        onChange={(evento) => cambiar('desafioMes', evento.target.value)}
                      />
                      <Boton type="submit" cargando={ocupado('crear-desafio')}>
                        Crear desafío
                      </Boton>
                    </form>
                  </Tarjeta>

                  <Tarjeta>
                    <h3 className="text-base font-bold text-tinta-900">Elegir ganador</h3>
                    <form onSubmit={(evento) => { void enviarGanador(evento) }} className="mt-4 flex flex-col gap-4">
                      <Selector
                        etiqueta="Desafío"
                        id="ganador-desafio"
                        valor={form.desafioId}
                        opciones={[
                          { valor: '', texto: 'Selecciona un desafío' },
                          ...opcionesDesafios,
                        ]}
                        onChange={(valor) => cambiar('desafioId', valor)}
                      />
                      <Selector
                        etiqueta="Ganador"
                        id="ganador-usuario"
                        valor={form.ganadorId}
                        opciones={[
                          { valor: '', texto: 'Selecciona una cuenta' },
                          ...opcionesUsuarios,
                        ]}
                        onChange={(valor) => cambiar('ganadorId', valor)}
                      />
                      <Boton
                        type="submit"
                        cargando={ocupado('asignar-ganador')}
                        disabled={!form.desafioId || !form.ganadorId}
                      >
                        Asignar ganador
                      </Boton>
                    </form>
                  </Tarjeta>
                </div>

                {datos.desafios.elementos.length > 0 && (
                  <Tabla encabezados={['Mes', 'Título', 'Ganador']}>
                    {datos.desafios.elementos.map((desafio) => (
                      <tr key={desafio.id_desafio}>
                        <td className={CLASES_CELDA}>{formatearMes(desafio.mes)}</td>
                        <td className={CLASES_CELDA}>{desafio.titulo}</td>
                        <td className={CLASES_CELDA}>
                          {desafio.nombre_ganador ?? (
                            <span className="text-tinta-500">Sin asignar</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </Tabla>
                )}
              </section>
            )}

            {/* ----------------------------- Usuarios ----------------------------- */}
            {seccion === 'usuarios' && (
              <section aria-labelledby="titulo-usuarios">
                <h2 id="titulo-usuarios" className="text-xl font-bold text-tinta-900">
                  Cuentas registradas
                </h2>
                <p className="mt-2 text-sm text-tinta-600">
                  Desactivar una cuenta le impide entrar, sin borrar su historial. No puedes
                  desactivar tu propia cuenta de administrador.
                </p>
                <Tabla encabezados={['Nombre', 'Correo', 'Rol', 'Estado', 'Acción']}>
                  {datos.usuarios.elementos.map((cuenta) => (
                    <tr key={cuenta.id_usuario}>
                      <td className={CLASES_CELDA}>
                        <p className="font-semibold text-tinta-900">{cuenta.nombre}</p>
                        <p className="mt-0.5 text-xs text-tinta-500">{cuenta.region}</p>
                      </td>
                      <td className={CLASES_CELDA}>{cuenta.correo}</td>
                      <td className={CLASES_CELDA}>{cuenta.rol}</td>
                      <td className={CLASES_CELDA}>
                        <Etiqueta tono={cuenta.activo ? 'exito' : 'neutro'}>
                          {cuenta.activo ? 'activa' : 'inactiva'}
                        </Etiqueta>
                      </td>
                      <td className={CLASES_CELDA}>
                        <Boton
                          variante="secundario"
                          tamano="sm"
                          cargando={ocupado(`usuario-${cuenta.id_usuario}`)}
                          onClick={() => {
                            void ejecutar(
                              `usuario-${cuenta.id_usuario}`,
                              () => adminApi.cambiarEstadoUsuario(cuenta.id_usuario, !cuenta.activo),
                              cuenta.activo ? 'Cuenta desactivada.' : 'Cuenta reactivada.',
                            )
                          }}
                        >
                          {cuenta.activo ? 'Desactivar' : 'Reactivar'}
                        </Boton>
                      </td>
                    </tr>
                  ))}
                </Tabla>
              </section>
            )}

            {/* ----------------------------- Comunidad ---------------------------- */}
            {seccion === 'comunidad' && (
              <section aria-labelledby="titulo-comunidad">
                <h2 id="titulo-comunidad" className="text-xl font-bold text-tinta-900">
                  Tiendas y grupos
                </h2>
                <div className="mt-5 grid gap-5 lg:grid-cols-2">
                  <Tarjeta>
                    <h3 className="text-base font-bold text-tinta-900">Nueva tienda</h3>
                    <form onSubmit={(evento) => { void enviarTienda(evento) }} className="mt-4 flex flex-col gap-4">
                      <Campo
                        etiqueta="Nombre"
                        id="tienda-nombre"
                        required
                        minLength={2}
                        value={form.tiendaNombre}
                        onChange={(evento) => cambiar('tiendaNombre', evento.target.value)}
                      />
                      <Selector
                        etiqueta="Tipo"
                        id="tienda-tipo"
                        valor={form.tiendaTipo}
                        opciones={TIPOS_TIENDA.map((tipo) => ({
                          valor: tipo,
                          texto: ETIQUETAS_TIPO_TIENDA[tipo],
                        }))}
                        onChange={(valor) => cambiar('tiendaTipo', valor as Tienda['tipo'])}
                      />
                      <Selector
                        etiqueta="Región"
                        id="tienda-region"
                        valor={form.tiendaRegion}
                        opciones={opcionesRegiones}
                        onChange={(valor) => cambiar('tiendaRegion', valor)}
                      />
                      <Campo
                        etiqueta="Sitio web"
                        id="tienda-enlace"
                        type="url"
                        placeholder="https://…"
                        value={form.tiendaEnlace}
                        onChange={(evento) => cambiar('tiendaEnlace', evento.target.value)}
                      />
                      <Boton type="submit" cargando={ocupado('crear-tienda')}>
                        Agregar tienda
                      </Boton>
                    </form>
                  </Tarjeta>

                  <Tarjeta>
                    <h3 className="text-base font-bold text-tinta-900">Nuevo grupo</h3>
                    <form onSubmit={(evento) => { void enviarGrupo(evento) }} className="mt-4 flex flex-col gap-4">
                      <Campo
                        etiqueta="Nombre"
                        id="grupo-nombre"
                        required
                        minLength={2}
                        value={form.grupoTitulo}
                        onChange={(evento) => cambiar('grupoTitulo', evento.target.value)}
                      />
                      <Selector
                        etiqueta="Plataforma"
                        id="grupo-plataforma"
                        valor={form.grupoPlataforma}
                        opciones={PLATAFORMAS.map((plataforma) => ({
                          valor: plataforma,
                          texto: ETIQUETAS_PLATAFORMA[plataforma],
                        }))}
                        onChange={(valor) => cambiar('grupoPlataforma', valor as Grupo['plataforma'])}
                      />
                      <Selector
                        etiqueta="Región"
                        id="grupo-region"
                        valor={form.grupoRegion}
                        opciones={opcionesRegiones}
                        onChange={(valor) => cambiar('grupoRegion', valor)}
                      />
                      <Campo
                        etiqueta="Enlace"
                        id="grupo-enlace"
                        type="url"
                        placeholder="https://…"
                        value={form.grupoEnlace}
                        onChange={(evento) => cambiar('grupoEnlace', evento.target.value)}
                      />
                      <Boton type="submit" cargando={ocupado('crear-grupo')}>
                        Agregar grupo
                      </Boton>
                    </form>
                  </Tarjeta>
                </div>

                <div className="mt-8 grid gap-5 lg:grid-cols-2">
                  <div>
                    <h3 className="text-base font-bold text-tinta-900">
                      Tiendas ({datos.tiendas.total})
                    </h3>
                    <ul className="mt-3 space-y-2 text-sm">
                      {datos.tiendas.elementos.map((tienda) => (
                        <li key={tienda.id_tienda} className="rounded-control border border-tinta-200 bg-white px-3 py-2">
                          {tienda.nombre} · {ETIQUETAS_TIPO_TIENDA[tienda.tipo]}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-tinta-900">
                      Grupos ({datos.grupos.total})
                    </h3>
                    <ul className="mt-3 space-y-2 text-sm">
                      {datos.grupos.elementos.map((grupo) => (
                        <li key={grupo.id_comunidad} className="rounded-control border border-tinta-200 bg-white px-3 py-2">
                          {grupo.nombre} · {ETIQUETAS_PLATAFORMA[grupo.plataforma]}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </Disposicion>
  )
}
