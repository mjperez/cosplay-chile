import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { useMeta } from '../../contexto/MetaContext'
import SubirImagen from '../../components/SubirImagen'
import useApi from '../../components/useApi'
import { Alerta, AreaTexto, Campo, EncabezadoPagina, Selector, useTitulo } from '../../components/ui'

const CLAVE_BORRADOR = 'cosplaychile.borrador-tutorial'
const VACIO = {
  tipo: 'GUIA', titulo: '', descripcion: '', cuerpo: '', nivel: 'PRINCIPIANTE', categoria_id: '',
  imagen: null, video_url: '', pasos: '', materiales: '', entrevistado: '', qa: [{ p: '', r: '' }], enlaces: '',
}

function leerBorrador() {
  try {
    const b = JSON.parse(localStorage.getItem(CLAVE_BORRADOR) || 'null')
    return b && typeof b === 'object' ? { ...VACIO, ...b } : null
  } catch {
    return null
  }
}

function guardarBorrador(f) {
  try {
    localStorage.setItem(CLAVE_BORRADOR, JSON.stringify(f))
  } catch {
    /* sin almacenamiento local: el borrador vive solo en la pestaña */
  }
}

function borrarBorrador() {
  try {
    localStorage.removeItem(CLAVE_BORRADOR)
  } catch {
    /* nada que borrar */
  }
}

const lineas = (t) => t.split('\n').map((s) => s.trim()).filter(Boolean)

// UC6 «Gestionar Tutoriales — publicar un tutorial» (Tabla 6, Figs. 13 y 15)
export default function PublicarTutorial() {
  useTitulo('Publicar un tutorial')
  const { opciones } = useMeta()
  const navigate = useNavigate()
  const { datos: categorias } = useApi('/api/categorias')
  const borradorInicial = useRef(leerBorrador())
  const [form, setForm] = useState(borradorInicial.current || VACIO)
  const [recuperado, setRecuperado] = useState(Boolean(borradorInicial.current?.titulo || borradorInicial.current?.descripcion))
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [exito, setExito] = useState(null)
  const resumenError = useRef(null)

  // Excepción 1: el borrador se guarda en cada cambio por si la sesión expira
  useEffect(() => {
    if (!exito) guardarBorrador(form)
  }, [form, exito])

  const set = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }))
  const err = (c) => error?.campos?.[c]

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    const cuerpo = {
      tipo: form.tipo, titulo: form.titulo, descripcion: form.descripcion, cuerpo: form.cuerpo, nivel: form.nivel,
      categoria_id: form.categoria_id, video_url: form.video_url || null,
      imagen_url: form.imagen?.url || null, imagen_alt: form.imagen?.alt || null,
    }
    if (form.tipo === 'GUIA') Object.assign(cuerpo, { pasos: lineas(form.pasos), materiales: lineas(form.materiales) })
    if (form.tipo === 'ENTREVISTA') {
      const qa = form.qa.filter((x) => x.p.trim() || x.r.trim())
      Object.assign(cuerpo, { entrevistado: form.entrevistado, preguntas: qa.map((x) => x.p), respuestas: qa.map((x) => x.r) })
    }
    if (form.tipo === 'ARTICULO') cuerpo.enlaces = lineas(form.enlaces)
    try {
      const r = await api('/api/contenidos', { method: 'POST', body: cuerpo })
      borrarBorrador()
      setExito(r)
    } catch (e2) {
      if (e2.status === 401) {
        // Sesión expirada durante la edición: borrador guardado y redirección al Caso de Uso Cero
        navigate('/ingresar?siguiente=/guias/publicar')
        return
      }
      if (e2.message === 'Categoría no encontrada') e2.campos = { ...e2.campos, categoria_id: 'Categoría no encontrada. Elige otra de la lista.' }
      setError(e2)
      setTimeout(() => resumenError.current?.focus(), 0)
    } finally {
      setEnviando(false)
    }
  }

  const migas = [{ a: '/', texto: 'Inicio' }, { a: '/guias', texto: 'Guías' }, { texto: 'Enviar un tutorial' }]
  const pasos = ['Envío', 'Pendiente de revisión', 'Publicado y notificado']
  const indicador = (actual) => (
    <ol className="mt-8 flex flex-wrap gap-x-8 gap-y-3" aria-label="Estado del envío">
      {pasos.map((p, i) => (
        <li key={p} className="flex items-center gap-3" aria-current={i === actual ? 'step' : undefined}>
          <span
            aria-hidden="true"
            className={`inline-flex size-9 items-center justify-center rounded-full font-bold ${
              i <= actual ? 'bg-linear-120 from-coral to-fucsia text-tinta-oscura' : 'border border-white/40 text-white'
            }`}
          >
            {i + 1}
          </span>
          <span className={`text-sm ${i === actual ? 'font-bold text-white' : 'text-lavanda'}`}>{p}</span>
        </li>
      ))}
    </ol>
  )

  if (exito) {
    return (
      <div className="pb-24">
        <EncabezadoPagina migas={migas} titulo="¡Envío recibido!">
          {indicador(1)}
        </EncabezadoPagina>
        <div className="contenedor mt-10 max-w-3xl">
          <Alerta tipo="exito">{exito.mensaje}</Alerta>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to={`/guias/${exito.contenido.id}`} className="boton-marca">Ver mi envío</Link>
            <Link to="/perfil#mis-envios" className="boton-contorno">Ver todos mis envíos</Link>
            <button className="boton-texto" onClick={() => { setForm(VACIO); setExito(null) }}>Publicar otro</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={migas}
        titulo="Envía tu tutorial"
        bajada="Comparte lo que sabes. Tu envío queda pendiente de revisión y el equipo de moderación te avisará cuando se publique."
      >
        {indicador(0)}
      </EncabezadoPagina>
      <div className="contenedor mt-10 max-w-4xl">
        {recuperado && (
          <Alerta tipo="info" className="mb-4">
            Recuperamos tu borrador guardado.{' '}
            <button className="enlace-claro" onClick={() => { setForm(VACIO); setRecuperado(false) }}>Empezar de cero</button>
          </Alerta>
        )}
        <form onSubmit={enviar} className="panel space-y-6 p-6 sm:p-8" noValidate>
          {error && (
            <div ref={resumenError} tabIndex={-1}>
              <Alerta tipo="error">{error.message}</Alerta>
            </div>
          )}
          <fieldset>
            <legend className="sobretitulo mb-3">Formato</legend>
            <div className="flex flex-wrap gap-2">
              {opciones('tipos_contenido').map((o) => (
                <label
                  key={o.valor}
                  className={`chip-filtro has-[input:focus-visible]:outline-2 has-[input:focus-visible]:outline-cian ${
                    form.tipo === o.valor ? 'border-transparent bg-linear-120 from-coral to-fucsia font-bold text-tinta-oscura' : ''
                  }`}
                >
                  <input type="radio" name="tipo" value={o.valor} checked={form.tipo === o.valor} onChange={set('tipo')} className="sr-only" />
                  {o.texto}
                </label>
              ))}
            </div>
          </fieldset>

          <Campo etiqueta="Título" requerido maxLength={200} value={form.titulo} onChange={set('titulo')} error={err('titulo')} placeholder="Ej.: Guantes articulados en EVA" />
          <AreaTexto etiqueta="Descripción breve" requerido rows={2} maxLength={500} value={form.descripcion} onChange={set('descripcion')}
            error={err('descripcion')} ayuda="Entre 10 y 500 caracteres. Aparece en el listado de guías." />
          <div className="grid gap-5 sm:grid-cols-2">
            <Selector etiqueta="Categoría" requerido vacio="Elige una categoría"
              opciones={(categorias || []).map((c) => ({ valor: c.id, texto: c.nombre }))}
              value={form.categoria_id} onChange={set('categoria_id')} error={err('categoria_id')} />
            <Selector etiqueta="Nivel" requerido opciones={opciones('niveles')} value={form.nivel} onChange={set('nivel')} />
          </div>
          <AreaTexto etiqueta="Contenido" rows={6} value={form.cuerpo} onChange={set('cuerpo')} error={err('cuerpo')}
            placeholder="Cuéntanos qué se aprende, materiales y tiempos"
            ayuda="Separa los párrafos con una línea en blanco. Usa «## » al inicio para un subtítulo y «- » para listas." />

          {form.tipo === 'GUIA' && (
            <div className="grid gap-5 sm:grid-cols-2">
              <AreaTexto etiqueta="Materiales (uno por línea)" requerido rows={5} value={form.materiales} onChange={set('materiales')} error={err('materiales')} />
              <AreaTexto etiqueta="Pasos (uno por línea, en orden)" requerido rows={5} value={form.pasos} onChange={set('pasos')} error={err('pasos')} />
            </div>
          )}
          {form.tipo === 'ENTREVISTA' && (
            <fieldset className="space-y-3">
              <legend className="sobretitulo mb-3">Entrevista</legend>
              <Campo etiqueta="Persona entrevistada" requerido value={form.entrevistado} onChange={set('entrevistado')} />
              {form.qa.map((x, i) => (
                <div key={i} className="rounded-panel border border-white/16 p-4">
                  <Campo etiqueta={`Pregunta ${i + 1}`} value={x.p}
                    onChange={(e) => setForm((f) => ({ ...f, qa: f.qa.map((y, j) => (j === i ? { ...y, p: e.target.value } : y)) }))} />
                  <AreaTexto etiqueta={`Respuesta ${i + 1}`} rows={2} value={x.r} className="mt-3"
                    onChange={(e) => setForm((f) => ({ ...f, qa: f.qa.map((y, j) => (j === i ? { ...y, r: e.target.value } : y)) }))} />
                  {form.qa.length > 1 && (
                    <button type="button" className="boton-texto mt-1" onClick={() => setForm((f) => ({ ...f, qa: f.qa.filter((_, j) => j !== i) }))}>
                      Quitar pregunta {i + 1}
                    </button>
                  )}
                </div>
              ))}
              <button type="button" className="boton-contorno" onClick={() => setForm((f) => ({ ...f, qa: [...f.qa, { p: '', r: '' }] }))}>
                Agregar pregunta
              </button>
            </fieldset>
          )}
          {form.tipo === 'ARTICULO' && (
            <AreaTexto etiqueta="Enlaces de referencia (uno por línea)" requerido rows={3} value={form.enlaces} onChange={set('enlaces')}
              error={err('enlaces')} ayuda="Deben comenzar con https://" />
          )}

          <section aria-labelledby="t-multimedia" className="space-y-4">
            <h2 id="t-multimedia" className="sobretitulo">Multimedia (opcional)</h2>
            {form.imagen ? (
              <div className="flex items-center gap-4">
                <img src={form.imagen.url} alt={form.imagen.alt} className="h-20 w-28 object-cover" />
                <button type="button" className="boton-texto" onClick={() => setForm((f) => ({ ...f, imagen: null }))}>Quitar imagen</button>
              </div>
            ) : (
              <SubirImagen etiqueta="Imagen principal" onSubida={(img) => setForm((f) => ({ ...f, imagen: img }))} />
            )}
            <Campo etiqueta="Video de YouTube o Vimeo" type="url" value={form.video_url} onChange={set('video_url')}
              error={err('video_url')} placeholder="https://www.youtube.com/watch?v=…" />
          </section>

          <div className="flex flex-wrap items-center gap-4 border-t border-white/12 pt-6">
            <button className="boton-marca boton-grande" disabled={enviando}>{enviando ? 'Enviando…' : 'Enviar a revisión'}</button>
            <span className="text-sm text-lavanda">Tu borrador se guarda automáticamente en este navegador.</span>
          </div>
        </form>
      </div>
    </div>
  )
}