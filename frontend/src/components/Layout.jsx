import { startTransition, useEffect, useId, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexto/AuthContext'
import { Alerta } from './ui'
import CampanaNotificaciones from './CampanaNotificaciones'
import BuscadorGlobal from './BuscadorGlobal'
import Icono from './diseno/Icono'
import Logo from './diseno/Logo'
import bandaLuces from '../assets/diseno/banda-luces.jpg'

const SECCIONES = [
  { a: '/guias', texto: 'Guías' },
  { a: '/directorio', texto: 'Directorio' },
  { a: '/calendario', texto: 'Calendario' },
  { a: '/comunidad', texto: 'Comunidad', tambien: ['/desafios'] },
]

function claseNav(activa) {
  return `inline-flex min-h-11 items-center border-b-2 px-0.5 text-[15px] font-medium text-white no-underline transition-colors hover:border-white/50 ${
    activa ? 'border-coral' : 'border-transparent'
  }`
}

function MenuCuenta({ usuario, esAdmin, onSalir }) {
  const [abierto, setAbierto] = useState(false)
  const caja = useRef(null)
  const boton = useRef(null)
  const location = useLocation()

  useEffect(() => setAbierto(false), [location.pathname])
  useEffect(() => {
    if (!abierto) return
    const fuera = (e) => !caja.current?.contains(e.target) && setAbierto(false)
    const tecla = (e) => {
      if (e.key === 'Escape') {
        setAbierto(false)
        boton.current?.focus()
      }
    }
    document.addEventListener('mousedown', fuera)
    document.addEventListener('keydown', tecla)
    return () => {
      document.removeEventListener('mousedown', fuera)
      document.removeEventListener('keydown', tecla)
    }
  }, [abierto])

  const inicial = (usuario.nombre || '?').trim().charAt(0).toUpperCase()
  const enlaces = [
    { a: '/perfil', texto: 'Mi perfil', icono: 'usuario' },
    { a: '/favoritos', texto: 'Mis favoritos', icono: 'corazon' },
    { a: '/guias/publicar', texto: 'Enviar un tutorial', icono: 'libro' },
    ...(esAdmin ? [{ a: '/moderacion', texto: 'Panel de moderación', icono: 'escudo' }] : []),
  ]
  return (
    <div className="relative" ref={caja}>
      <button
        ref={boton}
        className="inline-flex min-h-11 items-center gap-2 rounded-full py-1 pl-1 pr-2 text-white hover:text-durazno"
        aria-expanded={abierto}
        aria-controls="menu-cuenta"
        onClick={() => setAbierto((v) => !v)}
      >
        <span aria-hidden="true" className="inline-flex size-9 items-center justify-center rounded-full bg-linear-135 from-coral to-fucsia font-bold text-tinta-oscura">
          {inicial}
        </span>
        <span className="sr-only">Menú de mi cuenta,</span>
        <span className="max-w-32 truncate text-sm font-medium">{usuario.nombre}</span>
        <Icono nombre="abajo" tamano={14} grosor={2.2} />
      </button>
      {abierto && (
        <div id="menu-cuenta" className="absolute right-0 z-[600] mt-2 w-60 rounded-[18px] border border-white/16 bg-panel p-2 shadow-2xl">
          <ul>
            {enlaces.map((e) => (
              <li key={e.a}>
                <Link to={e.a} className="flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm text-white no-underline hover:bg-white/8 hover:text-durazno">
                  <Icono nombre={e.icono} tamano={18} className="text-durazno" />
                  {e.texto}
                </Link>
              </li>
            ))}
            <li className="mt-1 border-t border-white/12 pt-1">
              <button onClick={onSalir} className="flex min-h-11 w-full items-center gap-3 rounded-lg px-3 text-left text-sm text-white hover:bg-white/8 hover:text-durazno">
                <Icono nombre="salir" tamano={18} className="text-durazno" />
                Cerrar sesión
              </button>
            </li>
          </ul>
        </div>
      )}
    </div>
  )
}

function Encabezado({ enPortada }) {
  const { usuario, esAdmin, cerrarSesion } = useAuth()
  const [menuAbierto, setMenuAbierto] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => setMenuAbierto(false), [location.pathname])

  const salir = () => {
    // Navegación y cierre en la misma transición: así RequiereSesion no alcanza a redirigir a /ingresar
    navigate('/')
    startTransition(cerrarSesion)
  }
  const activa = (s) => location.pathname.startsWith(s.a) || s.tambien?.some((t) => location.pathname.startsWith(t))

  return (
    <header className={`${enPortada ? 'absolute inset-x-0 top-0' : 'relative'} z-[500]`}>
      <div className="flex flex-wrap items-center gap-x-9 gap-y-3 px-gutter py-[22px]">
        <Logo />
        <nav aria-label="Principal" className="hidden flex-1 justify-center lg:flex">
          <ul className="flex flex-wrap gap-x-[30px]">
            {SECCIONES.map((s) => (
              <li key={s.a}>
                <NavLink to={s.a} className={() => claseNav(activa(s))} aria-current={activa(s) ? 'page' : undefined}>
                  {s.texto}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="ml-auto flex items-center gap-3 lg:ml-0">
          {!enPortada && (
            <div className="hidden xl:block">
              <BuscadorGlobal />
            </div>
          )}
          {usuario ? (
            <>
              <CampanaNotificaciones />
              <div className="hidden lg:block">
                <MenuCuenta usuario={usuario} esAdmin={esAdmin} onSalir={salir} />
              </div>
            </>
          ) : (
            <div className="hidden items-center gap-3 lg:flex">
              <Link to="/ingresar" className="boton-texto no-underline">Ingresar</Link>
              <Link to="/registro" className="boton-contorno">Registrarse</Link>
            </div>
          )}
          <button
            className="inline-flex min-h-11 items-center gap-2 rounded-full border border-white/40 px-4 text-sm font-medium text-white lg:hidden"
            aria-expanded={menuAbierto}
            aria-controls="menu-movil"
            onClick={() => setMenuAbierto((v) => !v)}
          >
            <Icono nombre={menuAbierto ? 'cerrar' : 'menu'} tamano={18} />
            Menú
          </button>
        </div>
      </div>

      {/* Menú móvil (mobile-first): buscador, secciones y cuenta */}
      <div id="menu-movil" hidden={!menuAbierto} className="border-y border-white/12 bg-panel/97 px-gutter pb-6 pt-4 lg:hidden">
        <BuscadorGlobal />
        <nav aria-label="Principal (móvil)" className="mt-4">
          <ul className="grid gap-1">
            {SECCIONES.map((s) => (
              <li key={s.a}>
                <NavLink
                  to={s.a}
                  aria-current={activa(s) ? 'page' : undefined}
                  className={`flex min-h-12 items-center border-l-2 pl-3 font-display text-xl font-bold text-white no-underline ${activa(s) ? 'border-coral' : 'border-transparent'}`}
                >
                  {s.texto}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="mt-5 border-t border-white/12 pt-4">
          {usuario ? (
            <ul className="grid gap-1 text-[15px]">
              <li><Link to="/perfil" className="flex min-h-11 items-center text-white">Mi perfil</Link></li>
              <li><Link to="/favoritos" className="flex min-h-11 items-center text-white">Mis favoritos</Link></li>
              <li><Link to="/guias/publicar" className="flex min-h-11 items-center text-white">Enviar un tutorial</Link></li>
              {esAdmin && <li><Link to="/moderacion" className="flex min-h-11 items-center text-white">Panel de moderación</Link></li>}
              <li><button onClick={salir} className="flex min-h-11 items-center text-durazno">Cerrar sesión</button></li>
            </ul>
          ) : (
            <div className="flex flex-wrap gap-3">
              <Link to="/ingresar" className="boton-contorno">Ingresar</Link>
              <Link to="/registro" className="boton-marca">Registrarse</Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

function ColumnaPie({ titulo, enlaces }) {
  const id = useId()
  return (
    <nav aria-labelledby={id} className="min-w-[140px] flex-[1_1_150px]">
      <h2 id={id} className="mb-3 font-display text-lg font-bold text-white">{titulo}</h2>
      <ul>
        {enlaces.map((e) => (
          <li key={e.texto}>
            <Link to={e.a} className="flex min-h-9 items-center text-sm text-lavanda no-underline hover:text-white">
              {e.texto}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}

function Pie() {
  const { usuario, esAdmin } = useAuth()
  const cuenta = usuario
    ? [
        { a: '/perfil', texto: 'Mi perfil' },
        { a: '/favoritos', texto: 'Mis favoritos' },
        { a: '/guias/publicar', texto: 'Envía un tutorial' },
        { a: '/calendario/sugerir', texto: 'Sugiere un evento' },
      ]
    : [
        { a: '/ingresar', texto: 'Ingresar' },
        { a: '/registro', texto: 'Crear cuenta' },
        { a: '/guias/publicar', texto: 'Envía un tutorial' },
        { a: '/calendario/sugerir', texto: 'Sugiere un evento' },
      ]
  const seguridad = [
    { a: '/seguridad', texto: 'Reportar contenido' },
    { a: '/seguridad#consejos', texto: 'Seguridad en eventos' },
    { a: '/contacto', texto: 'Contacto' },
    { a: '/privacidad', texto: 'Privacidad y tus datos' },
    ...(esAdmin ? [{ a: '/moderacion', texto: 'Panel de moderación' }] : []),
  ]
  return (
    <footer>
      <div aria-hidden="true" className="h-[200px] bg-cover bg-center" style={{ backgroundImage: `url(${bandaLuces})` }} />
      <div className="flex flex-wrap gap-x-14 gap-y-10 bg-noche px-gutter pb-10 pt-14">
        <div className="flex min-w-[260px] flex-[2_1_320px] flex-col gap-4">
          <Logo />
          <p className="max-w-[420px] text-[15px] leading-relaxed text-lavanda">
            El punto de encuentro del cosplay en Chile: guías, profesionales, tiendas, eventos y comunidad, reunidos en un solo sitio y gratis.
          </p>
          {/* Redes de la plataforma: aún no existen (placeholder, ver docs/BRECHAS_DISENO.md) */}
          <ul className="flex flex-wrap gap-2" aria-label="Redes sociales (próximamente)">
            {['Instagram', 'TikTok', 'Discord', 'YouTube'].map((r) => (
              <li key={r} className="inline-flex min-h-9 items-center rounded-full border border-white/35 px-3.5 text-[13px] text-white">
                {r}
              </li>
            ))}
          </ul>
        </div>
        <ColumnaPie
          titulo="Explora"
          enlaces={[
            { a: '/guias', texto: 'Guías' },
            { a: '/directorio', texto: 'Directorio' },
            { a: '/calendario', texto: 'Calendario' },
            { a: '/comunidad', texto: 'Comunidad' },
            { a: '/desafios', texto: 'Desafíos mensuales' },
          ]}
        />
        <ColumnaPie titulo="Tu cuenta" enlaces={cuenta} />
        <ColumnaPie titulo="Seguridad" enlaces={seguridad} />
      </div>
      <div className="flex flex-wrap justify-between gap-x-8 gap-y-2 border-t border-white/12 bg-noche px-gutter py-5 text-[13px] text-lavanda">
        <span>© 2026 Cosplay Chile. Plataforma gratuita; no procesa pagos ni vende entradas.</span>
        <span>
          Tus datos se tratan conforme a la <Link to="/privacidad" className="enlace-claro">Ley 21.719</Link>, con consentimiento explícito y derecho a supresión.
        </span>
      </div>
    </footer>
  )
}

export default function Layout() {
  const { sesionExpirada, limpiarAvisoSesion } = useAuth()
  const location = useLocation()
  const principal = useRef(null)
  const primeraCarga = useRef(true)
  const enPortada = location.pathname === '/'

  // Al cambiar de página se mueve el foco al contenido (lectores de pantalla, RNF-03)
  useEffect(() => {
    if (primeraCarga.current) {
      primeraCarga.current = false
      return
    }
    if (!location.hash) principal.current?.focus({ preventScroll: false })
  }, [location.pathname, location.hash])

  // Enlaces a una sección de otra página (#consejos, #faq, #sugerir…): se desplaza y se enfoca su encabezado
  useEffect(() => {
    if (!location.hash) return
    const t = setTimeout(() => {
      const destino = document.getElementById(decodeURIComponent(location.hash.slice(1)))
      if (!destino) return
      destino.scrollIntoView({ block: 'start' })
      const titulo = destino.querySelector('h2, h3')
      if (titulo) {
        titulo.setAttribute('tabindex', '-1')
        titulo.focus({ preventScroll: true })
      }
    }, 50)
    return () => clearTimeout(t)
  }, [location.pathname, location.hash])

  const aviso = sesionExpirada && (
    <Alerta tipo="aviso" className="mb-6">
      Tu sesión expiró.{' '}
      <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname)}`} className="enlace-claro" onClick={limpiarAvisoSesion}>
        Vuelve a iniciar sesión
      </Link>{' '}
      para continuar.
    </Alerta>
  )

  return (
    <div className="relative flex min-h-screen flex-col overflow-x-clip bg-[linear-gradient(180deg,#0d0924_0%,#1a0d3c_24%,#2b1550_50%,#170c33_76%,#0c0820_100%)]">
      <a href="#contenido" className="sr-only-focusable fixed left-2 top-2 z-[1000] rounded bg-cian px-4 py-2 font-bold text-tinta-oscura">
        Saltar al contenido principal
      </a>
      <Encabezado enPortada={enPortada} />

      <main id="contenido" ref={principal} tabIndex={-1} className="w-full flex-1 outline-none">
        {aviso && <div className={`contenedor ${enPortada ? 'pt-28' : 'pt-4'}`}>{aviso}</div>}
        <Outlet />
      </main>

      <Pie />
    </div>
  )
}
