// Cliente de la API REST. Todos los textos de error se muestran en español de Chile.
const CLAVE_TOKEN = 'cosplaychile.token'

// En desarrollo Vite hace de proxy de /api y /media. En producción el sitio
// estático y la API viven en servicios distintos: VITE_API_URL apunta a la API
// y sus rutas relativas /media/... se convierten en URL absolutas al leerlas.
const BASE = String(import.meta.env?.VITE_API_URL || '').replace(/\/$/, '')

function conBase(ruta) {
  return BASE && ruta?.startsWith('/') ? `${BASE}${ruta}` : ruta
}

function absolutizarMedia(valor) {
  if (!BASE) return valor
  if (Array.isArray(valor)) return valor.map(absolutizarMedia)
  if (valor && typeof valor === 'object') {
    for (const clave of Object.keys(valor)) valor[clave] = absolutizarMedia(valor[clave])
    return valor
  }
  return typeof valor === 'string' && valor.startsWith('/media/') ? `${BASE}${valor}` : valor
}

export function obtenerToken() {
  try {
    return localStorage.getItem(CLAVE_TOKEN)
  } catch {
    return null
  }
}

export function guardarToken(token) {
  try {
    if (token) localStorage.setItem(CLAVE_TOKEN, token)
    else localStorage.removeItem(CLAVE_TOKEN)
  } catch {
    /* almacenamiento no disponible: la sesión dura lo que la pestaña */
  }
}

const TRADUCCIONES = [
  [/^Value error, /, ''],
  [/value is not a valid email address.*/i, 'Ingresa un correo electrónico válido'],
  [/^Field required$/, 'Este campo es obligatorio'],
  [/String should have at least (\d+) characters?/, 'Debe tener al menos $1 caracteres'],
  [/String should have at most (\d+) characters?/, 'Debe tener como máximo $1 caracteres'],
  [/List should have at most (\d+) items?.*/, 'Máximo $1 elementos'],
  [/Input should be a valid integer.*/, 'Debe ser un número entero'],
  [/Input should be greater than or equal to (\d+)/, 'Debe ser mayor o igual a $1'],
  [/Input should be less than or equal to (\d+)/, 'Debe ser menor o igual a $1'],
  [/Input should be a valid (date|URL).*/, 'Formato no válido'],
  [/Input should be .*/, 'Valor no válido'],
]

export function traducir(msg = '') {
  let texto = String(msg)
  for (const [patron, reemplazo] of TRADUCCIONES) texto = texto.replace(patron, reemplazo)
  return texto
}

export class ApiError extends Error {
  constructor(status, detalle) {
    let mensaje = 'Ocurrió un error inesperado. Intenta nuevamente.'
    const campos = {}
    let codigo = null
    if (typeof detalle === 'string') mensaje = detalle
    else if (Array.isArray(detalle)) {
      for (const e of detalle) {
        const campo = (e.loc || []).filter((p) => p !== 'body').join('.')
        if (campo && !campos[campo]) campos[campo] = traducir(e.msg)
      }
      mensaje = Object.keys(campos).length ? 'Revisa los campos marcados.' : traducir(detalle[0]?.msg)
    } else if (detalle && typeof detalle === 'object') {
      mensaje = detalle.mensaje || mensaje
      codigo = detalle.codigo || null
    }
    super(mensaje)
    this.status = status
    this.campos = campos
    this.codigo = codigo
  }
}

export async function api(ruta, { method = 'GET', body, form, signal } = {}) {
  const headers = {}
  const token = obtenerToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let cuerpo
  if (form) cuerpo = form
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    cuerpo = JSON.stringify(body)
  }
  let resp
  try {
    resp = await fetch(conBase(ruta), { method, headers, body: cuerpo, signal })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new ApiError(0, 'No pudimos conectar con el servidor. Revisa tu conexión.')
  }
  if (resp.status === 204) return null
  const tipo = resp.headers.get('content-type') || ''
  const datos = tipo.includes('application/json') ? await resp.json() : await resp.text()
  if (!resp.ok) {
    if (resp.status === 401 && token) {
      window.dispatchEvent(new CustomEvent('sesion-expirada'))
    }
    throw new ApiError(resp.status, typeof datos === 'object' ? datos.detail : datos)
  }
  return absolutizarMedia(datos)
}

// Descarga un archivo de una ruta protegida (envía el token y entrega el archivo al navegador)
export async function descargar(ruta, nombrePorDefecto = 'archivo') {
  const token = obtenerToken()
  const resp = await fetch(conBase(ruta), { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!resp.ok) {
    let detalle
    try {
      detalle = (await resp.json()).detail
    } catch {
      detalle = undefined
    }
    if (resp.status === 401 && token) window.dispatchEvent(new CustomEvent('sesion-expirada'))
    throw new ApiError(resp.status, detalle)
  }
  const disposicion = resp.headers.get('content-disposition') || ''
  const nombre = /filename="([^"]+)"/.exec(disposicion)?.[1] || nombrePorDefecto
  const url = URL.createObjectURL(await resp.blob())
  const a = document.createElement('a')
  a.href = url
  a.download = nombre
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function qs(params) {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(params || {})) {
    if (v !== undefined && v !== null && v !== '') p.set(k, v)
  }
  const s = p.toString()
  return s ? `?${s}` : ''
}
