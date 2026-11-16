import { useId, useState } from 'react'
import { api } from '../api/client'
import Icono from './diseno/Icono'

const MAX_MB = 5
const TIPOS = ['image/png', 'image/jpeg', 'image/webp']

/**
 * Sube una imagen mediante /api/archivos (Adapter de almacenamiento en el backend)
 * y exige texto alternativo antes de entregarla (accesibilidad, RNF-03).
 */
export default function SubirImagen({ etiqueta = 'Imagen', onSubida, textoBoton = 'Agregar imagen', altInicial = '' }) {
  const id = useId()
  const [archivo, setArchivo] = useState(null)
  const [alt, setAlt] = useState(altInicial)
  const [error, setError] = useState('')
  const [subiendo, setSubiendo] = useState(false)

  const elegir = (e) => {
    setError('')
    const f = e.target.files?.[0]
    if (!f) return
    if (!TIPOS.includes(f.type)) {
      setError('Solo se aceptan imágenes JPG, PNG o WebP.')
      e.target.value = ''
      return
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      // UC6, excepción 2: se rechaza indicando el límite admitido
      setError(`El archivo pesa ${(f.size / 1024 / 1024).toFixed(1)} MB y supera el máximo permitido de ${MAX_MB} MB.`)
      e.target.value = ''
      return
    }
    setArchivo(f)
  }

  const subir = async () => {
    if (!archivo) return setError('Primero elige una imagen.')
    if (alt.trim().length < 3) return setError('Describe la imagen en el texto alternativo (mínimo 3 caracteres).')
    setSubiendo(true)
    setError('')
    try {
      const form = new FormData()
      form.append('archivo', archivo)
      const r = await api('/api/archivos', { method: 'POST', form })
      onSubida({ url: r.url, alt: alt.trim() })
      setArchivo(null)
      setAlt('')
      document.getElementById(`${id}-archivo`).value = ''
    } catch (e) {
      setError(e.message)
    } finally {
      setSubiendo(false)
    }
  }

  return (
    <fieldset className="rounded-panel border border-dashed p-4" style={{ borderColor: 'var(--campo-borde)' }}>
      <legend className="rotulo px-1">{etiqueta}</legend>
      <label htmlFor={`${id}-archivo`} className="rotulo flex items-center gap-2">
        <Icono nombre="subir" tamano={16} /> Archivo (JPG, PNG o WebP, máximo {MAX_MB} MB)
      </label>
      <input
        id={`${id}-archivo`}
        type="file"
        accept={TIPOS.join(',')}
        onChange={elegir}
        className="mt-2 block w-full text-sm text-[var(--texto-suave)] file:mr-3 file:min-h-11 file:cursor-pointer file:rounded-xs file:border file:border-[var(--contorno)] file:bg-transparent file:px-4 file:text-xs file:font-bold file:uppercase file:tracking-[.12em] file:text-[var(--texto-contorno)]"
        aria-describedby={error ? `${id}-error` : undefined}
      />
      <label htmlFor={`${id}-alt`} className="rotulo mt-3">
        Texto alternativo: describe lo que se ve en la imagen
      </label>
      <input
        id={`${id}-alt`}
        className="campo"
        value={alt}
        maxLength={300}
        onChange={(e) => setAlt(e.target.value)}
        placeholder="Ej.: Cosplayer con armadura de goma EVA pintada en dorado"
      />
      {error && (
        <p id={`${id}-error`} role="alert" className="mensaje-error mt-2">
          {error}
        </p>
      )}
      <button type="button" className="boton-contorno mt-3" onClick={subir} disabled={subiendo}>
        {subiendo ? 'Subiendo…' : textoBoton}
      </button>
    </fieldset>
  )
}
