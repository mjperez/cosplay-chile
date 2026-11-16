// Convierte un enlace de Cosplay Chile en el objeto que espera POST /api/reportes ({tipo_objeto, objeto_id}).
// La API exige el id del contenido: no existe el reporte "por URL" ni anónimo (ver docs/BRECHAS_DISENO.md).
const UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

const REGLAS = [
  { patron: new RegExp(`^/comunidad/temas/${UUID}$`, 'i'), tipo: 'TEMA', texto: 'Tema del foro' },
  { patron: new RegExp(`^/guias/(${UUID})$`, 'i'), tipo: 'CONTENIDO', texto: 'Guía o tutorial' },
  { patron: new RegExp(`^/calendario/(${UUID})$`, 'i'), tipo: 'EVENTO', texto: 'Evento publicado' },
  { patron: new RegExp(`^/directorio/(${UUID})$`, 'i'), tipo: 'DIRECTORIO', texto: 'Ficha del directorio' },
]

export function analizarEnlace(texto, origen = window.location.origin) {
  const limpio = (texto || '').trim()
  if (!limpio) return null
  let url
  try {
    url = new URL(limpio, origen)
  } catch {
    return null
  }
  if (url.origin !== new URL(origen).origin) return null
  const ruta = url.pathname.replace(/\/+$/, '')
  // Una respuesta del foro se enlaza como /comunidad/temas/<id>#respuesta-<id>
  const respuesta = new RegExp(`^#respuesta-(${UUID})$`, 'i').exec(url.hash)
  if (respuesta && /^\/comunidad\/temas\//.test(ruta)) {
    return { tipo_objeto: 'RESPUESTA', objeto_id: respuesta[1].toLowerCase(), texto: 'Respuesta en el foro' }
  }
  for (const r of REGLAS) {
    if (r.patron.test(ruta)) {
      const id = ruta.match(new RegExp(UUID, 'i'))[0].toLowerCase()
      return { tipo_objeto: r.tipo, objeto_id: id, texto: r.texto }
    }
  }
  return null
}
