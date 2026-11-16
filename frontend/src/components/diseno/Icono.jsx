// Íconos de trazo del diseño (viewBox 24×24). Siempre decorativos: el texto accesible lo pone quien los usa.
const TRAZOS = {
  buscar: <><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></>,
  abajo: <path d="M5 9l7 7 7-7" />,
  derecha: <path d="M9 5l7 7-7 7" />,
  izquierda: <path d="M15 5l-7 7 7 7" />,
  libro: <><path d="M4 4h10a4 4 0 0 1 4 4v12H8a4 4 0 0 1-4-4z" /><path d="M8 9h6M8 13h6" /></>,
  tienda: <><path d="M3 9l2-5h14l2 5" /><path d="M4 9v11h16V9" /><path d="M9 20v-6h6v6" /></>,
  calendario: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></>,
  chat: <><path d="M4 5h16v11H9l-5 4z" /><path d="M8 9h8M8 12h5" /></>,
  personas: <><circle cx="9" cy="8" r="3.5" /><path d="M2 20c0-3.5 3-5.5 7-5.5s7 2 7 5.5" /><circle cx="17" cy="9" r="2.5" /><path d="M17 14.5c3 0 5 1.5 5 4" /></>,
  corazon: <path d="M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.5A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11z" />,
  salud: <><path d="M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.5A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11z" /><path d="M7 11h3l1.5-3 2 6 1.5-3h2" /></>,
  compartir: <><circle cx="6" cy="12" r="2.5" /><circle cx="18" cy="6" r="2.5" /><circle cx="18" cy="18" r="2.5" /><path d="M8.2 10.8l7.6-3.6M8.2 13.2l7.6 3.6" /></>,
  reloj: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  video: <><circle cx="12" cy="12" r="9" /><path d="M10 8.5l6 3.5-6 3.5z" /></>,
  descargar: <path d="M12 4v11M7 11l5 5 5-5M5 20h14" />,
  subir: <path d="M12 16V5M7 9l5-5 5 5M5 20h14" />,
  ubicacion: <><path d="M12 21s7-6 7-12a7 7 0 0 0-14 0c0 6 7 12 7 12z" /><circle cx="12" cy="9" r="2.5" /></>,
  alerta: <><path d="M12 3l10 18H2z" /><path d="M12 10v5M12 18h.01" /></>,
  estrella: <path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" />,
  escudo: <><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /><path d="M9 12l2 2 4-4" /></>,
  mas: <path d="M12 5v14M5 12h14" />,
  ojo: <><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></>,
  check: <path d="M5 12l5 5 9-10" />,
  bandera: <path d="M5 21V4M5 5h13l-2 4 2 4H5" />,
  campana: <><path d="M6 17v-6a6 6 0 0 1 12 0v6l2 2H4z" /><path d="M10 21h4" /></>,
  cerrar: <path d="M6 6l12 12M18 6L6 18" />,
  externo: <path d="M7 17L17 7M9 7h8v8" />,
  lista: <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />,
  imagen: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="2" /><path d="M4 18l5-5 4 4 3-3 4 4" /></>,
  correo: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></>,
  transporte: <><rect x="4" y="3" width="16" height="15" rx="3" /><path d="M4 11h16M8 21v-3M16 21v-3" /><circle cx="8" cy="15" r=".8" /><circle cx="16" cy="15" r=".8" /></>,
  candado: <><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></>,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  salir: <path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10" />,
  usuario: <><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.5-6.5 8-6.5s8 2.5 8 6.5" /></>,
  trofeo: <><path d="M8 4h8v5a4 4 0 0 1-8 0z" /><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8 21h8M9 17h6" /></>,
  enlace: <path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" />,
}

export default function Icono({ nombre, tamano = 20, grosor = 1.8, className = '', relleno = 'none', ...props }) {
  return (
    <svg
      width={tamano}
      height={tamano}
      viewBox="0 0 24 24"
      fill={relleno}
      stroke="currentColor"
      strokeWidth={grosor}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={`block flex-none ${className}`}
      {...props}
    >
      {TRAZOS[nombre]}
    </svg>
  )
}
