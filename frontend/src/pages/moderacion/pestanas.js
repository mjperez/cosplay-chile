import Bitacora from './Bitacora'
import ColaContenidos from './ColaContenidos'
import Contactos from './Contactos'
import DesafiosAdmin from './DesafiosAdmin'
import EventosPendientes from './EventosPendientes'
import Reportes from './Reportes'
import Usuarios from './Usuarios'

// Secciones del panel. «contador» = campo de /api/moderacion/resumen
export const PESTANAS = [
  { id: 'contenidos', texto: 'Tutoriales pendientes', contador: 'contenidos_pendientes', Componente: ColaContenidos },
  { id: 'reportes', texto: 'Reportes de contenido', contador: 'reportes_abiertos', Componente: Reportes },
  { id: 'contactos', texto: 'Mensajes de contacto', contador: 'contactos_nuevos', Componente: Contactos },
  { id: 'eventos', texto: 'Eventos sugeridos', contador: 'eventos_pendientes', Componente: EventosPendientes },
  { id: 'usuarios', texto: 'Usuarios', Componente: Usuarios },
  { id: 'desafios', texto: 'Desafíos', Componente: DesafiosAdmin },
  { id: 'bitacora', texto: 'Bitácora', Componente: Bitacora },
]
