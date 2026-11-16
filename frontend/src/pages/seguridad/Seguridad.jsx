import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import { useMeta } from '../../contexto/MetaContext'
import Acordeon from '../../components/diseno/Acordeon'
import Icono from '../../components/diseno/Icono'
import Pestanas from '../../components/diseno/Pestanas'
import { Alerta, AreaTexto, Campo, Casilla, EncabezadoPagina, Selector, useTitulo } from '../../components/ui'
import mucama from '../../assets/diseno/mucama.jpg'
import { analizarEnlace } from './enlaceReportable'

const CONSEJOS = [
  ['Acoso y respeto', 'Eventos', 'Pedir consentimiento antes de una foto o un abrazo, decir que no sin dar explicaciones y avisar al staff del evento. Disfrazarse no es una invitación.'],
  ['Traslado seguro', 'Transporte', 'Define con anticipación cómo llegas y cómo vuelves, avisa a alguien de confianza y viaja acompañado si el trayecto es de noche. Evita cambiarte en lugares no habilitados.'],
  ['Salud en convención', 'Salud', 'Hidrátate, planifica descansos y evita trajes sin ventilación en días de calor. Lleva a mano lo esencial y conoce dónde está la zona de primeros auxilios.'],
  ['Armas de utilería', 'Eventos', 'Revisa las reglas de cada evento sobre réplicas y accesorios. Que sea evidente que es de utilería y no lo uses fuera del recinto.'],
  ['Tratos y compras seguras', 'Compras', 'Revisa reseñas y portafolio antes de pagar a un proveedor, deja todo por escrito y desconfía de pagos íntegros por adelantado a cuentas desconocidas.'],
  ['Cuida tus datos', 'Cuenta', 'No compartas documentos ni tu dirección en el foro. Usa una contraseña distinta y reporta perfiles falsos o intentos de estafa.'],
]

function Recibido({ texto, onOtro }) {
  return (
    <div className="space-y-4" role="status">
      <h2 className="font-display text-3xl font-bold text-white">Recibimos tu mensaje</h2>
      <p className="text-[15px] text-lavanda">{texto} El equipo de moderación lo revisará manualmente.</p>
      <button type="button" className="boton-contorno" onClick={onOtro}>Enviar otro mensaje</button>
    </div>
  )
}

// RF-38: reportar contenido inapropiado a partir de su enlace
function FormReporte() {
  const { usuario } = useAuth()
  const { opciones } = useMeta()
  const location = useLocation()
  const [enlace, setEnlace] = useState('')
  const [motivo, setMotivo] = useState('INAPROPIADO')
  const [detalle, setDetalle] = useState('')
  const [error, setError] = useState('')
  const [listo, setListo] = useState('')
  const [enviando, setEnviando] = useState(false)
  const objeto = analizarEnlace(enlace)

  if (!usuario) {
    return (
      <div className="space-y-4">
        <p className="text-[15px] text-lavanda">
          Para mantener la trazabilidad, reportar requiere una cuenta. Solo el equipo de moderación ve quién envía cada reporte.
        </p>
        <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname + location.search)}`} className="boton-marca boton-grande">
          Ingresar para reportar
        </Link>
        <p className="text-sm text-lavanda">
          ¿Es una denuncia grave o no tienes cuenta? Usa la pestaña «Contacto y denuncias».
        </p>
      </div>
    )
  }
  if (listo) return <Recibido texto={listo} onOtro={() => { setListo(''); setEnlace(''); setDetalle('') }} />

  const enviar = async (e) => {
    e.preventDefault()
    setError('')
    if (!objeto) {
      setError('Pega el enlace de una guía, tema del foro, evento o ficha del directorio de Cosplay Chile.')
      return
    }
    setEnviando(true)
    try {
      const r = await api('/api/reportes', { method: 'POST', body: { tipo_objeto: objeto.tipo_objeto, objeto_id: objeto.objeto_id, motivo, detalle } })
      setListo(r.mensaje)
    } catch (err) {
      setError(err.message)
    } finally {
      setEnviando(false)
    }
  }
  return (
    <form onSubmit={enviar} className="space-y-5" noValidate aria-label="Reportar contenido">
      <p className="text-[15px] text-lavanda">
        ¿Viste una publicación, comentario, evento o ficha que no respeta las normas? Cuéntanos dónde está y qué ocurrió.
      </p>
      <Alerta tipo="error">{error}</Alerta>
      <Campo
        etiqueta="Enlace al contenido"
        requerido
        value={enlace}
        onChange={(e) => setEnlace(e.target.value)}
        placeholder="Pega aquí la dirección de la página"
        ayuda={objeto ? `Detectamos: ${objeto.texto}.` : 'Copia la dirección desde la barra del navegador. Para reseñas y fotos de desafíos usa el botón «Reportar» junto a ellas.'}
      />
      <Selector
        etiqueta="Motivo"
        opciones={opciones('motivos_reporte').filter((o) => o.valor !== 'ACTUALIZACION_EVENTO' || objeto?.tipo_objeto === 'EVENTO')}
        value={motivo}
        onChange={(e) => setMotivo(e.target.value)}
      />
      <AreaTexto etiqueta="Detalle" rows={4} maxLength={2000} value={detalle} onChange={(e) => setDetalle(e.target.value)} placeholder="Describe brevemente lo que viste" />
      <button className="boton-marca boton-grande" disabled={enviando}>{enviando ? 'Enviando…' : 'Enviar reporte'}</button>
    </form>
  )
}

// RF-40: dudas, sugerencias o denuncias al equipo
function FormContacto({ tipoInicial }) {
  const { usuario } = useAuth()
  const { opciones } = useMeta()
  const inicial = () => ({
    nombre: usuario?.nombre || '',
    email: usuario?.email || '',
    tipo: tipoInicial || 'DUDA',
    asunto: tipoInicial === 'CUENTA' ? 'Mi cuenta aparece suspendida' : '',
    mensaje: '',
  })
  const [datos, setDatos] = useState(inicial)
  const [autoriza, setAutoriza] = useState(false)
  const [error, setError] = useState(null)
  const [enviado, setEnviado] = useState('')
  // La sesión se carga de forma asíncrona: se completan nombre y correo cuando llega, sin pisar lo escrito
  useEffect(() => {
    if (usuario) setDatos((d) => ({ ...d, nombre: d.nombre || usuario.nombre, email: d.email || usuario.email }))
  }, [usuario])
  const cambiar = (c) => (e) => setDatos((d) => ({ ...d, [c]: e.target.value }))
  const c = (n) => error?.campos?.[n]

  if (enviado) return <Recibido texto={enviado} onOtro={() => { setEnviado(''); setDatos(inicial()); setAutoriza(false) }} />

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    if (!autoriza) {
      setError({ message: 'Para responderte necesitamos tu autorización para usar tus datos.', campos: { autoriza: 'Marca la casilla para continuar' } })
      return
    }
    try {
      const r = await api('/api/contacto', { method: 'POST', body: datos })
      setEnviado(r.mensaje)
    } catch (err) {
      setError(err)
    }
  }
  return (
    <form onSubmit={enviar} className="space-y-5" noValidate aria-label="Contacto y denuncias">
      <p className="text-[15px] text-lavanda">
        Escríbenos por consultas, sugerencias o para hacer una denuncia. Responde un equipo humano, no un sistema automático.
      </p>
      <Alerta tipo="error">{error?.message}</Alerta>
      <div className="grid gap-5 sm:grid-cols-2">
        <Campo etiqueta="Nombre" requerido value={datos.nombre} onChange={cambiar('nombre')} error={c('nombre')} autoComplete="name" placeholder="Cómo te llamas" />
        <Campo etiqueta="Correo para responderte" type="email" requerido value={datos.email} onChange={cambiar('email')} error={c('email')} autoComplete="email" placeholder="tu@correo.cl" />
      </div>
      <Selector etiqueta="Motivo" opciones={opciones('tipos_contacto')} value={datos.tipo} onChange={cambiar('tipo')} />
      <Campo etiqueta="Asunto" requerido value={datos.asunto} onChange={cambiar('asunto')} error={c('asunto')} />
      <AreaTexto
        etiqueta="Mensaje"
        requerido
        rows={5}
        value={datos.mensaje}
        onChange={cambiar('mensaje')}
        error={c('mensaje')}
        placeholder="Cuéntanos en qué podemos ayudarte"
        ayuda={datos.tipo === 'DENUNCIA' ? 'Incluye enlaces o fechas si los tienes. Tu denuncia es confidencial.' : undefined}
      />
      <Casilla
        etiqueta="Autorizo el uso de mis datos para responder este mensaje, conforme a la Ley 21.719."
        checked={autoriza}
        onChange={(e) => setAutoriza(e.target.checked)}
        error={c('autoriza')}
      />
      <button className="boton-marca boton-grande">Enviar mensaje</button>
    </form>
  )
}

// RF-38, RF-39 y RF-40: reportar, contactar y consejos de seguridad
export default function Seguridad({ pestanaInicial = 'reporte' }) {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const tipoContacto = params.get('tipo')
  const pestana = pestanaInicial
  useTitulo(pestana === 'contacto' ? 'Contacto y denuncias' : 'Seguridad y contacto')

  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { texto: 'Seguridad y contacto' }]}
        titulo="Seguridad y contacto"
        bajada="Esta comunidad se cuida entre todos. Aquí puedes reportar contenido inapropiado, escribirnos o hacer una denuncia, y revisar consejos para vivir los eventos con tranquilidad."
      />
      <div className="contenedor mt-10 grid grid-cols-1 items-start gap-8 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <section className="panel p-6 sm:p-8" aria-label="Formularios">
          <Pestanas
            etiqueta="Qué quieres hacer"
            idPanel="panel-seguridad"
            className="mb-6"
            pestanas={[{ valor: 'reporte', texto: 'Reportar contenido' }, { valor: 'contacto', texto: 'Contacto y denuncias' }]}
            valor={pestana}
            onCambiar={(v) => navigate(v === 'contacto' ? '/contacto' : '/seguridad', { replace: true })}
          />
          <div id="panel-seguridad" role="tabpanel" aria-labelledby={`panel-seguridad-tab-${pestana}`}>
            {pestana === 'contacto' ? <FormContacto tipoInicial={tipoContacto} /> : <FormReporte />}
          </div>
        </section>

        <aside className="flex flex-col gap-6" aria-label="Ayuda">
          <div className="border border-peligro/50 bg-peligro/10 p-6">
            <h2 className="flex items-center gap-2 font-display text-2xl font-bold text-white">
              <Icono nombre="alerta" tamano={20} className="text-peligro" /> Si es una urgencia
            </h2>
            <p className="mt-3 text-[15px] leading-relaxed text-white">
              Esta plataforma no reemplaza a los servicios de emergencia. Si tú o alguien está en riesgo, llama de inmediato a{' '}
              <strong>Carabineros (133)</strong>, <strong>Ambulancia (131)</strong> o <strong>Bomberos (132)</strong>.
            </p>
          </div>
          <div className="panel p-6">
            <h2 className="font-display text-2xl font-bold text-white">Cómo revisamos los reportes</h2>
            <ol className="mt-4 space-y-3 text-sm text-lavanda">
              {[
                'Moderación revisa cada reporte manualmente.',
                'Puede descartarlo, resolverlo u ocultar el contenido.',
                'Las cuentas con faltas graves se suspenden.',
              ].map((t, i) => (
                <li key={t} className="flex gap-3">
                  <span aria-hidden="true" className="font-display text-xl leading-none font-bold text-durazno">{i + 1}</span> {t}
                </li>
              ))}
            </ol>
          </div>
        </aside>
      </div>

      <section id="consejos" aria-labelledby="t-consejos" className="contenedor mt-24 scroll-mt-6">
        <div className="grid grid-cols-1 items-start gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
          <div>
            <p className="sobretitulo">Consejos de seguridad</p>
            <h2 id="t-consejos" className="titulo-seccion mt-3">Cuídate y cuida a los demás</h2>
            <p className="mt-4 text-[15px] leading-relaxed text-lavanda">
              Recomendaciones de la comunidad y del equipo para que asistir a un evento, comprar o conversar en línea sea una buena experiencia.
            </p>
            <img src={mucama} alt="" className="mt-8 hidden aspect-[4/5] w-full max-w-sm object-cover lg:block" />
            <Link to="/guias?categoria=seguridad-eventos" className="boton-contorno mt-8">Guías de seguridad en eventos</Link>
          </div>
          <Acordeon items={CONSEJOS.map(([titulo, etiqueta, contenido]) => ({ titulo, etiqueta, contenido }))} />
        </div>
      </section>
    </div>
  )
}
