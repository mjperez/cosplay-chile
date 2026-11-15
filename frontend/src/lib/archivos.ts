/** Subida de imágenes a través del patrón Adapter del backend. */

import { peticionModulo } from './modulos'

export interface ArchivoPublico {
  identificador: string
  enlace: string
  tipo_mime: string
  tamano: number
}

export const archivosApi = {
  subir: (archivo: File) => {
    const datos = new FormData()
    datos.append('archivo', archivo)
    // No se fija Content-Type: el navegador debe añadir el boundary del
    // multipart. `peticionModulo` detecta FormData y no fuerza JSON.
    return peticionModulo<ArchivoPublico>('/api/v1/archivos', {
      method: 'POST',
      body: datos,
    })
  },

  eliminar: (identificador: string) =>
    peticionModulo<void>(
      `/api/v1/archivos/${identificador}`,
      { method: 'DELETE' },
    ),
}
