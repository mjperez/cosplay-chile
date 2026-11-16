import SubirImagen from './SubirImagen'
import { Campo } from './ui'

// RF-27: subir fotos de cosplay con crédito al fotógrafo y al cosplayer
export function CamposFotoCreditos({ valor, onCambiar, obligatoria = false, errores = {} }) {
  const { imagen, credito_fotografo = '', credito_cosplayer = '' } = valor
  const set = (campo) => (e) => onCambiar({ ...valor, [campo]: e.target.value })
  return (
    <fieldset className="space-y-4 rounded-panel border p-4" style={{ borderColor: 'var(--borde)' }}>
      <legend className="rotulo px-1">Foto {obligatoria ? '' : '(opcional)'} con créditos</legend>
      <p className="ayuda mt-0">Da crédito a quien tomó la foto y a quien hace el cosplay. Si es tuya, escribe «Autorretrato».</p>
      {imagen ? (
        <div className="flex flex-wrap items-center gap-4">
          <img src={imagen.url} alt={imagen.alt} className="h-24 w-32 object-cover" />
          <button type="button" className="boton-contorno" onClick={() => onCambiar({ ...valor, imagen: null })}>Quitar foto</button>
        </div>
      ) : (
        <SubirImagen etiqueta="Foto" onSubida={(img) => onCambiar({ ...valor, imagen: img })} />
      )}
      {errores.imagen_url && <p role="alert" className="mensaje-error">{errores.imagen_url}</p>}
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo etiqueta="Crédito fotografía" requerido={Boolean(imagen) || obligatoria} value={credito_fotografo} onChange={set('credito_fotografo')} placeholder="@fotografo" />
        <Campo etiqueta="Crédito cosplayer" requerido={Boolean(imagen) || obligatoria} value={credito_cosplayer} onChange={set('credito_cosplayer')} placeholder="@cosplayer" />
      </div>
    </fieldset>
  )
}

export function payloadFoto(valor) {
  if (!valor.imagen) return {}
  return {
    imagen_url: valor.imagen.url,
    imagen_alt: valor.imagen.alt,
    credito_fotografo: valor.credito_fotografo || null,
    credito_cosplayer: valor.credito_cosplayer || null,
  }
}

// Foto con el pie de créditos del diseño (degradado sobre la imagen)
export function FiguraConCreditos({ url, alt, fotografo, cosplayer, className = '', proporcion = '' }) {
  if (!url) return null
  return (
    <figure className={`relative m-0 ${className}`}>
      <img src={url} alt={alt || ''} className={`block w-full object-cover ${proporcion}`} loading="lazy" />
      <figcaption className="absolute inset-x-0 bottom-0 bg-linear-to-b from-transparent to-[rgba(8,5,24,.9)] px-3.5 pb-3 pt-8 text-[12.5px] text-white">
        {cosplayer && <span className="block">Cosplay: {cosplayer}</span>}
        {fotografo && <span className="block">Foto: {fotografo}</span>}
      </figcaption>
    </figure>
  )
}
