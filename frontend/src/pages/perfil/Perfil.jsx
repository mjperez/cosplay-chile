import { startTransition, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import { useMeta } from '../../contexto/MetaContext'
import SubirImagen from '../../components/SubirImagen'
import Icono from '../../components/diseno/Icono'
import { Alerta, AreaTexto, Campo, EncabezadoPagina, GrupoChips, Selector, useTitulo } from '../../components/ui'
import { GRUPOS_FAVORITOS, ListaFavoritos, useListaFavoritos } from '../Favoritos'
import { PRESTADORES } from '../auth/Acceso'
import SeccionesExtraPerfil from './SeccionesExtraPerfil'

function FavoritosPerfil() {
  const { datos, aviso, quitar } = useListaFavoritos()
  const [tipo, setTipo] = useState('CONTENIDO')
  return (
    <section aria-labelledby="t-favs">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 id="t-favs" className="font-display text-2xl font-bold text-white">Mis favoritos</h2>
        <Link to="/favoritos" className="enlace-claro text-sm">Ver todos</Link>
      </div>
      <GrupoChips etiqueta="Tipo" valor={tipo} onCambiar={setTipo} opciones={GRUPOS_FAVORITOS.map((g) => ({ valor: g.tipo, texto: g.titulo }))} />
      <Alerta tipo="info" className="mt-3">{aviso}</Alerta>
      {datos && <ListaFavoritos items={datos.filter((f) => f.tipo === tipo).slice(0, 5)} onQuitar={quitar} />}
    </section>
  )
}

// Gestionar Perfil (UC4): RF-07, RF-08, RF-10 y derecho a supresión (RNF-11)
export default function Perfil() {
  useTitulo('Mi perfil')
  const { usuario, setUsuario, cerrarSesion } = useAuth()
  const { opciones, etiqueta } = useMeta()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [form, setForm] = useState(null)
  const [estado, setEstado] = useState({ ok: '', error: null })
  const [guardando, setGuardando] = useState(false)
  const [confirmarBorrado, setConfirmarBorrado] = useState('')

  useEffect(() => {
    if (usuario) {
      const p = usuario.perfil || {}
      setForm({
        nombre: usuario.nombre,
        tipo_perfil: p.tipo_perfil || 'COSPLAYER',
        region: p.region || '',
        biografia: p.biografia || '',
        especialidad: p.especialidad || '',
        disponibilidad: p.disponibilidad || '',
        redes_sociales: p.redes_sociales || [],
        portafolio: p.portafolio || [],
        perfil_publico: Boolean(p.perfil_publico),
      })
    }
  }, [usuario])

  if (!form) return null
  const cambiar = (c) => (e) => setForm((f) => ({ ...f, [c]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))
  const err = (c) => estado.error?.campos?.[c]

  const guardar = async (e) => {
    e?.preventDefault()
    setGuardando(true)
    setEstado({ ok: '', error: null })
    try {
      const u = await api('/api/perfil', {
        method: 'PUT',
        body: { ...form, region: form.region || null, redes_sociales: form.redes_sociales.filter((r) => r.url) },
      })
      setUsuario(u)
      setEstado({ ok: 'Tus cambios fueron guardados.', error: null })
    } catch (error) {
      setEstado({ ok: '', error })
    } finally {
      setGuardando(false)
    }
  }

  const redes = form.redes_sociales
  const setRed = (i, campo, valor) =>
    setForm((f) => ({ ...f, redes_sociales: f.redes_sociales.map((r, j) => (j === i ? { ...r, [campo]: valor } : r)) }))

  const eliminarCuenta = async () => {
    try {
      await api('/api/perfil', { method: 'DELETE' })
      // Primero se sale de la ruta protegida; si no, RequiereSesion redirige a /ingresar
      navigate('/?cuenta=eliminada', { replace: true })
      startTransition(cerrarSesion) // misma prioridad que la navegación (React Router usa transiciones)
    } catch (error) {
      setEstado({ ok: '', error })
    }
  }
  const inicial = (usuario.nombre || '?').charAt(0).toUpperCase()
  const esPrestador = PRESTADORES.includes(form.tipo_perfil)

  return (
    <div className="pb-24">
      <EncabezadoPagina migas={[{ a: '/', texto: 'Inicio' }, { texto: 'Mi perfil' }]} titulo="Gestiona tu perfil" bajada={`Sesión iniciada como ${usuario.email}`} />
      <div className="contenedor mt-10 grid grid-cols-1 items-start gap-8 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <div className="flex min-w-0 flex-col gap-8">
          {params.get('bienvenida') && <Alerta tipo="exito">¡Te damos la bienvenida a Cosplay Chile! Completa tu perfil cuando quieras.</Alerta>}
          <form onSubmit={guardar} className="panel space-y-6 p-6 sm:p-8" noValidate aria-labelledby="titulo-datos">
            <div className="flex flex-wrap items-center gap-5">
              <span aria-hidden="true" className="inline-flex size-24 flex-none items-center justify-center rounded-full border-2 border-coral bg-linear-135 from-coral to-fucsia font-display text-4xl font-bold text-tinta-oscura">
                {inicial}
              </span>
              <div className="min-w-0">
                <p className="sobretitulo">Gestionar perfil</p>
                <h2 id="titulo-datos" className="font-display text-3xl font-bold text-white">{usuario.nombre}</h2>
                <p className="mt-2 flex flex-wrap gap-2">
                  <span className="insignia bg-linear-120 from-coral to-fucsia text-tinta-oscura">{etiqueta('tipos_perfil', form.tipo_perfil)}</span>
                  <span className="etiqueta">
                    <Icono nombre="ojo" tamano={14} /> {form.perfil_publico ? (esPrestador ? 'Visible en el directorio' : 'Perfil público') : 'Perfil privado'}
                  </span>
                </p>
              </div>
            </div>
            <Alerta tipo="exito">{estado.ok}</Alerta>
            <Alerta tipo="error">{estado.error?.message}</Alerta>
            <div className="grid gap-5 sm:grid-cols-2">
              <Selector etiqueta="Región de procedencia" vacio="Prefiero no decir" opciones={opciones('regiones')} value={form.region} onChange={cambiar('region')} />
              <Campo etiqueta="Nombre o alias" requerido value={form.nombre} onChange={cambiar('nombre')} error={err('nombre')} />
              <Selector etiqueta="Tipo de perfil" opciones={opciones('tipos_perfil')} value={form.tipo_perfil} onChange={cambiar('tipo_perfil')} />
              <Campo etiqueta="Especialidad" value={form.especialidad} onChange={cambiar('especialidad')} placeholder="Ej.: armaduras de EVA" />
              <Campo etiqueta="Disponibilidad" value={form.disponibilidad} onChange={cambiar('disponibilidad')} placeholder="Ej.: encargos desde enero" className="sm:col-span-2" />
            </div>
            <AreaTexto etiqueta="Biografía" rows={4} maxLength={2000} value={form.biografia} onChange={cambiar('biografia')} error={err('biografia')}
              placeholder="Cuéntale a la comunidad quién eres y qué haces" />

            <fieldset className="space-y-3">
              <legend className="rotulo mb-1">Redes sociales</legend>
              {redes.map((r, i) => (
                <div key={i} className="flex flex-wrap items-end gap-3">
                  <Campo etiqueta={`Red ${i + 1}`} value={r.red} onChange={(e) => setRed(i, 'red', e.target.value)} className="w-36" />
                  <Campo etiqueta="Enlace" type="url" value={r.url} onChange={(e) => setRed(i, 'url', e.target.value)}
                    className="min-w-0 flex-1" error={err(`redes_sociales.${i}.url`)} placeholder="https://instagram.com/tu.usuario" />
                  <button type="button" className="boton-texto" onClick={() => setForm((f) => ({ ...f, redes_sociales: redes.filter((_, j) => j !== i) }))}>
                    Quitar<span className="sr-only"> red {i + 1}</span>
                  </button>
                </div>
              ))}
              {redes.length < 10 && (
                <div className="flex flex-wrap gap-2">
                  {['Instagram', 'TikTok', 'Otra red'].map((red) => (
                    <button key={red} type="button" className="boton-contorno" onClick={() => setForm((f) => ({ ...f, redes_sociales: [...redes, { red: red === 'Otra red' ? '' : red, url: '' }] }))}>
                      <Icono nombre="mas" tamano={14} grosor={2.2} /> {red}
                    </button>
                  ))}
                </div>
              )}
            </fieldset>

            <section aria-labelledby="titulo-portafolio" className="space-y-3">
              <h3 id="titulo-portafolio" className="rotulo">Portafolio fotográfico</h3>
              {form.portafolio.length > 0 ? (
                <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {form.portafolio.map((img, i) => (
                    <li key={img.url + i} className="relative">
                      <img src={img.url} alt={img.alt} className="aspect-square w-full object-cover" />
                      <button type="button" className="boton-texto w-full justify-center"
                        onClick={() => setForm((f) => ({ ...f, portafolio: f.portafolio.filter((_, j) => j !== i) }))}>
                        Quitar<span className="sr-only">: {img.alt}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-lavanda">Aún no agregas fotos a tu portafolio.</p>
              )}
              {form.portafolio.length < 20 && (
                <SubirImagen etiqueta="Subir foto al portafolio" textoBoton="Subir foto" onSubida={(img) => setForm((f) => ({ ...f, portafolio: [...f.portafolio, img] }))} />
              )}
            </section>

            <div className="flex items-start justify-between gap-4 border-y border-white/12 py-4">
              <div>
                <p id="lbl-pub" className="text-sm font-bold text-white">{esPrestador ? 'Mostrar mi perfil en el directorio público' : 'Hacer público mi perfil'}</p>
                <p id="ayuda-pub" className="mt-1 text-[13px] text-lavanda">
                  {esPrestador ? 'Aparecerás en el directorio con tu ficha. Puedes desactivarlo cuando quieras.' : 'Otras personas podrán ver tu biografía, redes y portafolio.'}
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={form.perfil_publico}
                aria-labelledby="lbl-pub"
                aria-describedby="ayuda-pub"
                onClick={() => setForm((f) => ({ ...f, perfil_publico: !f.perfil_publico }))}
                className={`relative h-7 w-12 flex-none rounded-full transition-colors ${form.perfil_publico ? 'bg-linear-120 from-coral to-fucsia' : 'bg-white/15'}`}
              >
                <span aria-hidden="true" className={`absolute top-[3px] size-[22px] rounded-full bg-white transition-all ${form.perfil_publico ? 'left-[23px]' : 'left-[3px]'}`} />
              </button>
            </div>
            <div className="flex flex-wrap gap-3">
              <button className="boton-marca boton-grande" disabled={guardando}>{guardando ? 'Guardando…' : 'Guardar cambios'}</button>
              {form.perfil_publico && <Link to={`/personas/${usuario.id}`} className="boton-contorno boton-grande">Ver mi perfil público</Link>}
            </div>
          </form>
          <div className="panel p-6 sm:p-8">
            <FavoritosPerfil />
          </div>
        </div>

        <div className="flex min-w-0 flex-col gap-8">
          <SeccionesExtraPerfil />
          <section className="panel border-peligro/40 p-6" aria-labelledby="titulo-eliminar">
            <h2 id="titulo-eliminar" className="font-display text-2xl font-bold text-peligro">Eliminar mi cuenta y mis datos</h2>
            <p className="mt-2 text-sm text-lavanda">
              Se borrarán tus datos personales, favoritos y notificaciones. Tus mensajes en foros quedarán como «Usuario eliminado». Esta acción no se
              puede deshacer (Ley 21.719, derecho a supresión).
            </p>
            <Campo etiqueta='Para confirmar escribe "ELIMINAR"' value={confirmarBorrado} onChange={(e) => setConfirmarBorrado(e.target.value)} className="mt-4 max-w-xs" />
            <button className="boton-peligro mt-4" disabled={confirmarBorrado !== 'ELIMINAR'} onClick={eliminarCuenta}>
              Eliminar mi cuenta definitivamente
            </button>
          </section>
        </div>
      </div>
    </div>
  )
}
