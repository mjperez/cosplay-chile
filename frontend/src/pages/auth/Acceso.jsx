import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import { useMeta } from '../../contexto/MetaContext'
import Icono from '../../components/diseno/Icono'
import Pestanas from '../../components/diseno/Pestanas'
import { Alerta, Campo, Casilla, EncabezadoPagina, Selector, useTitulo } from '../../components/ui'
import orejasGato from '../../assets/diseno/orejas-gato.jpg'

export const PRESTADORES = ['COSMAKER', 'SASTRE', 'MODELADOR', 'PINTOR', 'PELUQUERO', 'MAQUILLADOR', 'FOTOGRAFO', 'TIENDA']
const ROLES = [
  { valor: 'COSPLAYER', texto: 'Cosplayer' },
  { valor: 'COSMAKER', texto: 'Cosmaker o sastre' },
  { valor: 'FOTOGRAFO', texto: 'Fotógrafo' },
  { valor: 'TIENDA', texto: 'Tienda' },
  { valor: 'ORGANIZADOR', texto: 'Organizador' },
]
const RUTA = { login: '/ingresar', registro: '/registro', recuperar: '/recuperar' }

const destinoSeguro = (s, defecto) => (s && s.startsWith('/') && !s.startsWith('//') ? s : defecto)

// UC-01 Identificarse (Tabla 5)
function FormIngresar({ siguiente }) {
  const { iniciarSesion } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await iniciarSesion(email, password)
      navigate(destinoSeguro(siguiente, '/'), { replace: true }) // paso 6: redirige con sesión activa
    } catch (err) {
      setError(err)
    } finally {
      setEnviando(false)
    }
  }
  const suspendida = error?.codigo === 'CUENTA_SUSPENDIDA'

  return (
    <form onSubmit={enviar} className="space-y-5" noValidate aria-label="Iniciar sesión">
      {siguiente && !error && (
        <Alerta tipo="info">
          Inicia sesión para continuar.
          {siguiente.startsWith('/guias/publicar') && ' Tu borrador del tutorial quedó guardado y lo recuperarás al volver.'}
        </Alerta>
      )}
      {error && !suspendida && <Alerta tipo="error">{error.message}</Alerta>}
      {suspendida && (
        <Alerta tipo="error">
          <p>{error.message}</p>
          <Link to="/contacto?tipo=CUENTA" className="enlace-claro mt-2 inline-block">Escríbenos desde el formulario de contacto</Link>
        </Alerta>
      )}
      <Campo etiqueta="Correo electrónico" type="email" autoComplete="email" requerido value={email} onChange={(e) => setEmail(e.target.value)} placeholder="tu@correo.cl" />
      <Campo etiqueta="Contraseña" type="password" autoComplete="current-password" requerido value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Tu contraseña" />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to="/recuperar" className="enlace-claro text-sm">¿Olvidaste tu contraseña?</Link>
        <button className="boton-marca boton-grande" disabled={enviando}>{enviando ? 'Verificando…' : 'Entrar'}</button>
      </div>
    </form>
  )
}

// Flujo alterno 3a de UC-01 (RF-07, RF-10, RNF-11)
function FormRegistro({ siguiente, tipoInicial }) {
  const { registrarse } = useAuth()
  const { opciones } = useMeta()
  const navigate = useNavigate()
  const [datos, setDatos] = useState({
    nombre: '', email: '', password: '', tipo_perfil: tipoInicial || 'COSPLAYER', region: '', perfil_publico: false, acepta_privacidad: false,
  })
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const set = (campo, valor) => setDatos((d) => ({ ...d, [campo]: valor }))
  const cambiar = (campo) => (e) => set(campo, e.target.type === 'checkbox' ? e.target.checked : e.target.value)

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await registrarse({ ...datos, region: datos.region || null })
      navigate(destinoSeguro(siguiente, '/perfil?bienvenida=1'))
    } catch (err) {
      setError(err)
    } finally {
      setEnviando(false)
    }
  }
  const campo = (n) => error?.campos?.[n]
  const esPrestador = PRESTADORES.includes(datos.tipo_perfil)

  return (
    <form onSubmit={enviar} className="space-y-5" noValidate aria-label="Crear cuenta">
      <Alerta tipo="error">{error?.message}</Alerta>
      <fieldset>
        <legend className="rotulo mb-2">¿Cómo quieres participar?</legend>
        <div className="flex flex-wrap gap-2">
          {ROLES.map((r) => (
            <button key={r.valor} type="button" className="chip-filtro" aria-pressed={datos.tipo_perfil === r.valor} onClick={() => set('tipo_perfil', r.valor)}>
              {r.texto}
            </button>
          ))}
        </div>
        <Selector
          className="mt-3"
          etiqueta="Tipo de perfil (más opciones)"
          opciones={opciones('tipos_perfil')}
          value={datos.tipo_perfil}
          onChange={cambiar('tipo_perfil')}
        />
      </fieldset>
      <Campo etiqueta="Nombre o alias" requerido autoComplete="nickname" value={datos.nombre} onChange={cambiar('nombre')} error={campo('nombre')} placeholder="Cómo te verá la comunidad" />
      <Selector etiqueta="Región de procedencia" vacio="Prefiero no decir" opciones={opciones('regiones')} value={datos.region} onChange={cambiar('region')} />
      <Campo etiqueta="Correo electrónico" type="email" requerido autoComplete="email" value={datos.email} onChange={cambiar('email')} error={campo('email')} placeholder="tu@correo.cl" />
      <Campo
        etiqueta="Contraseña" type="password" requerido autoComplete="new-password" value={datos.password}
        onChange={cambiar('password')} error={campo('password')} ayuda="Mínimo 8 caracteres, con letras y números." placeholder="Mínimo 8 caracteres"
      />

      {esPrestador && (
        <div className="rounded-campo border border-white/16 p-4">
          <p className="flex items-center gap-2 font-display text-lg font-bold text-white">
            <Icono nombre="tienda" tamano={18} className="text-durazno" /> Registro para proveedores y tiendas
          </p>
          <p className="mt-2 text-sm text-lavanda">
            Al crear tu cuenta y activar la opción de abajo, se crea tu ficha en el directorio. Después la completas en tu perfil, en «Mi ficha»:
            nombre comercial, especialidades, servicios, precios, contacto y portafolio.
          </p>
        </div>
      )}

      <div className="flex items-start justify-between gap-4 border-y border-white/12 py-4">
        <div>
          <p id="lbl-publico" className="text-sm font-bold text-white">
            {esPrestador ? 'Visibilizar mi perfil en el directorio público' : 'Hacer público mi perfil'}
          </p>
          <p id="ayuda-publico" className="mt-1 text-[13px] text-lavanda">
            {datos.perfil_publico
              ? esPrestador ? 'Tu perfil aparecerá en el directorio público.' : 'Otras personas podrán ver tu biografía y portafolio.'
              : 'Opcional. Puedes cambiarlo cuando quieras.'}
          </p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={datos.perfil_publico}
          aria-labelledby="lbl-publico"
          aria-describedby="ayuda-publico"
          onClick={() => set('perfil_publico', !datos.perfil_publico)}
          className={`relative h-7 w-12 flex-none rounded-full transition-colors ${datos.perfil_publico ? 'bg-linear-120 from-coral to-fucsia' : 'bg-white/15'}`}
        >
          <span aria-hidden="true" className={`absolute top-[3px] size-[22px] rounded-full bg-white transition-all ${datos.perfil_publico ? 'left-[23px]' : 'left-[3px]'}`} />
        </button>
      </div>

      <div className="text-sm text-lavanda">
        <p className="font-bold text-white">¿Para qué usamos tus datos?</p>
        <p className="mt-1">
          Usamos tu correo para identificarte y avisarte de la actividad de tu cuenta, y tu región para mostrarte eventos y proveedores cercanos. No
          vendemos ni compartimos tus datos. <Link to="/privacidad" className="enlace-claro">Política de privacidad</Link>.
        </p>
      </div>
      <Casilla
        etiqueta="Acepto el tratamiento de mis datos personales conforme a la Ley 21.719, con la finalidad de gestionar mi cuenta. Puedo pedir su supresión cuando quiera."
        checked={datos.acepta_privacidad}
        onChange={cambiar('acepta_privacidad')}
        error={campo('acepta_privacidad')}
      />
      <button className="boton-marca boton-grande w-full" disabled={enviando}>{enviando ? 'Creando cuenta…' : 'Crear cuenta'}</button>
    </form>
  )
}

// Flujo alterno 3b de UC-01
function FormRecuperar() {
  const [email, setEmail] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      const r = await api('/api/auth/recuperar', { method: 'POST', body: { email } })
      setMensaje(r.mensaje)
    } catch (err) {
      setError(err)
    } finally {
      setEnviando(false)
    }
  }
  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-2xl font-bold text-white">Recupera tu contraseña</h2>
        <p className="mt-2 text-sm text-lavanda">Escribe el correo de tu cuenta y te enviaremos un enlace de restablecimiento. El enlace vence en 30 minutos.</p>
      </div>
      <Alerta tipo="exito">{mensaje}</Alerta>
      <Alerta tipo="error">{error?.message}</Alerta>
      {!mensaje && (
        <form onSubmit={enviar} className="space-y-5" noValidate aria-label="Recuperar contraseña">
          <Campo etiqueta="Correo electrónico" type="email" autoComplete="email" requerido value={email}
            onChange={(e) => setEmail(e.target.value)} error={error?.campos?.email} placeholder="tu@correo.cl" />
          <button className="boton-marca boton-grande w-full" disabled={enviando}>{enviando ? 'Enviando…' : 'Enviar enlace'}</button>
        </form>
      )}
      <Link to="/ingresar" className="boton-texto no-underline">
        <Icono nombre="izquierda" tamano={14} grosor={2.2} /> Volver a iniciar sesión
      </Link>
    </div>
  )
}

export default function Acceso({ modo = 'login' }) {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const siguiente = params.get('siguiente')
  useTitulo({ login: 'Ingresar', registro: 'Crear cuenta', recuperar: 'Recuperar contraseña' }[modo])
  const conSiguiente = (ruta) => (siguiente && modo !== 'recuperar' ? `${ruta}?siguiente=${encodeURIComponent(siguiente)}` : ruta)

  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { texto: 'Tu cuenta' }]}
        titulo="Entra o crea tu cuenta"
        bajada="Con una cuenta puedes guardar favoritos, enviar tutoriales, dejar reseñas, sugerir eventos y participar en el foro. Cada rol tiene un perfil propio."
      />
      <div className="contenedor mt-10 grid grid-cols-1 items-start gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
        <section className="panel p-6 sm:p-8" aria-label="Acceso">
          {modo === 'recuperar' ? (
            <FormRecuperar />
          ) : (
            <>
              <Pestanas
                etiqueta="Acceso a tu cuenta"
                idPanel="panel-acceso"
                className="mb-6"
                pestanas={[{ valor: 'login', texto: 'Iniciar sesión' }, { valor: 'registro', texto: 'Crear cuenta' }]}
                valor={modo}
                onCambiar={(v) => navigate(conSiguiente(RUTA[v]), { replace: true })}
              />
              <div id="panel-acceso" role="tabpanel" aria-labelledby={`panel-acceso-tab-${modo}`}>
                {modo === 'login' ? <FormIngresar siguiente={siguiente} /> : <FormRegistro siguiente={siguiente} tipoInicial={params.get('tipo')} />}
              </div>
            </>
          )}
          <p className="mt-6 flex items-center gap-2 text-[13px] text-lavanda">
            <Icono nombre="candado" tamano={15} /> Tus datos viajan cifrados y las contraseñas se guardan con encriptación.
          </p>
        </section>

        <aside aria-labelledby="t-beneficios" className="panel flex flex-col gap-6 p-6 sm:p-8">
          <div className="flex items-center gap-5">
            <img src={orejasGato} alt="" className="size-24 flex-none rounded-full border-2 border-coral object-cover" />
            <div>
              <p className="sobretitulo">Tu perfil</p>
              <h2 id="t-beneficios" className="font-display text-3xl font-bold text-white">Lo que puedes hacer con tu cuenta</h2>
            </div>
          </div>
          <ul className="space-y-4">
            {[
              ['corazon', 'Guardar guías, proveedores y eventos en favoritos.'],
              ['libro', 'Enviar tus tutoriales para que el equipo los publique.'],
              ['estrella', 'Dejar reseñas a profesionales y tiendas.'],
              ['calendario', 'Sugerir eventos y marcar «Asistiré».'],
              ['chat', 'Abrir temas en el foro y participar en los desafíos.'],
              ['tienda', 'Si ofreces servicios, aparecer en el directorio con tu ficha.'],
            ].map(([icono, texto]) => (
              <li key={texto} className="flex items-start gap-3 text-[15px] text-tinta">
                <Icono nombre={icono} tamano={20} className="mt-0.5 text-durazno" /> {texto}
              </li>
            ))}
          </ul>
          <p className="text-sm text-lavanda">
            Puedes explorar guías, directorio y calendario sin cuenta. Tus datos se tratan conforme a la Ley 21.719 y puedes eliminar tu cuenta cuando
            quieras.
          </p>
        </aside>
      </div>
    </div>
  )
}
