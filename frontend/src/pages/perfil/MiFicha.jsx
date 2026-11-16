import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { useMeta } from '../../contexto/MetaContext'
import SubirImagen from '../../components/SubirImagen'
import { Alerta, AreaTexto, Campo, Casilla, Selector } from '../../components/ui'

// RF-32: el prestador o la tienda completa su ficha (servicios, contacto, portafolio, precios, región)
export default function MiFicha() {
  const { opciones } = useMeta()
  const [ficha, setFicha] = useState(undefined)
  const [f, setF] = useState(null)
  const [estado, setEstado] = useState({ ok: '', error: null })

  useEffect(() => {
    api('/api/directorio/mi-ficha')
      .then((d) => {
        setFicha(d)
        setF({
          nombre: d.nombre, descripcion: d.descripcion || '', region: d.region || '', comuna: d.comuna || '',
          direccion: d.direccion || '', contacto: d.contacto || '', sitio_web: d.sitio_web || '',
          servicios: (d.servicios || []).join('\n'), especialidades: d.especialidades || [],
          precio_desde: d.precio_desde ?? '', precio_hasta: d.precio_hasta ?? '', portafolio: d.portafolio || [],
          tipos_producto: d.tipos_producto || [], alcance: d.alcance || 'NACIONAL', tienda_fisica: Boolean(d.tienda_fisica),
        })
      })
      .catch(() => setFicha(null))
  }, [])

  if (ficha === undefined) return null
  if (ficha === null) {
    return (
      <section className="panel p-6" aria-labelledby="t-ficha">
        <h2 id="t-ficha" className="font-display text-2xl font-bold text-white">Mi ficha en el directorio</h2>
        <p className="mt-2 text-sm text-lavanda">
          Si ofreces servicios (cosmaker, sastrería, maquillaje, fotografía…) o tienes una tienda, elige ese tipo de perfil y
          activa «Mostrar mi perfil en el directorio público» para aparecer en el directorio.
        </p>
      </section>
    )
  }

  const esTienda = ficha.tipo === 'TIENDA'
  const set = (c) => (e) => setF((x) => ({ ...x, [c]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))
  const alternarLista = (campo, valor) =>
    setF((x) => ({ ...x, [campo]: x[campo].includes(valor) ? x[campo].filter((v) => v !== valor) : [...x[campo], valor] }))
  const err = (c) => estado.error?.campos?.[c]

  const guardar = async (e) => {
    e.preventDefault()
    setEstado({ ok: '', error: null })
    const base = {
      nombre: f.nombre, descripcion: f.descripcion, region: f.region || null, comuna: f.comuna || null,
      direccion: f.direccion || null, contacto: f.contacto || null, sitio_web: f.sitio_web || null, portafolio: f.portafolio,
    }
    const extra = esTienda
      ? { tipos_producto: f.tipos_producto, alcance: f.alcance, tienda_fisica: f.tienda_fisica }
      : {
          servicios: f.servicios.split('\n').map((s) => s.trim()).filter(Boolean), especialidades: f.especialidades,
          precio_desde: f.precio_desde === '' ? null : Number(f.precio_desde), precio_hasta: f.precio_hasta === '' ? null : Number(f.precio_hasta),
        }
    try {
      setFicha(await api('/api/directorio/mi-ficha', { method: 'PUT', body: { ...base, ...extra } }))
      setEstado({ ok: 'Tu ficha fue actualizada.', error: null })
    } catch (error) {
      setEstado({ ok: '', error })
    }
  }

  return (
    <form onSubmit={guardar} className="panel space-y-5 p-6" aria-labelledby="t-ficha" noValidate>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="t-ficha" className="font-display text-2xl font-bold text-white">Mi ficha en el directorio</h2>
        <Link to={`/directorio/${ficha.id}`} className="enlace-claro text-sm">Ver mi ficha pública</Link>
      </div>
      <Alerta tipo="exito">{estado.ok}</Alerta>
      <Alerta tipo="error">{estado.error?.message}</Alerta>
      <Campo etiqueta="Nombre comercial" value={f.nombre} onChange={set('nombre')} error={err('nombre')} />
      <AreaTexto etiqueta="Descripción" rows={3} value={f.descripcion} onChange={set('descripcion')} />
      <div className="grid gap-4 sm:grid-cols-3">
        <Selector etiqueta="Región" vacio="Sin región" opciones={opciones('regiones')} value={f.region} onChange={set('region')} />
        <Campo etiqueta="Comuna" value={f.comuna} onChange={set('comuna')} />
        <Campo etiqueta="Dirección (opcional)" value={f.direccion} onChange={set('direccion')} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Campo etiqueta="Contacto (correo, teléfono o usuario)" value={f.contacto} onChange={set('contacto')} />
        <Campo etiqueta="Sitio web o red social" type="url" value={f.sitio_web} onChange={set('sitio_web')} error={err('sitio_web')} placeholder="https://" />
      </div>
      {esTienda ? (
        <>
          <fieldset>
            <legend className="rotulo">Productos que vendes</legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {opciones('tipos_producto').map((o) => (
                <Casilla key={o.valor} etiqueta={o.texto} checked={f.tipos_producto.includes(o.valor)} onChange={() => alternarLista('tipos_producto', o.valor)} />
              ))}
            </div>
          </fieldset>
          <div className="grid gap-4 sm:grid-cols-2">
            <Selector etiqueta="Origen" opciones={[{ valor: 'NACIONAL', texto: 'Nacional' }, { valor: 'INTERNACIONAL', texto: 'Internacional con envío a Chile' }]} value={f.alcance} onChange={set('alcance')} />
            <Casilla etiqueta="Tengo tienda física" checked={f.tienda_fisica} onChange={set('tienda_fisica')} className="self-end" />
          </div>
        </>
      ) : (
        <>
          <fieldset>
            <legend className="rotulo">Especialidades</legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {opciones('especialidades').map((o) => (
                <Casilla key={o.valor} etiqueta={o.texto} checked={f.especialidades.includes(o.valor)} onChange={() => alternarLista('especialidades', o.valor)} />
              ))}
            </div>
          </fieldset>
          <AreaTexto etiqueta="Servicios (uno por línea)" rows={4} value={f.servicios} onChange={set('servicios')} />
          <div className="grid gap-4 sm:grid-cols-2">
            <Campo etiqueta="Precio desde (CLP)" type="number" min="0" step="1000" value={f.precio_desde} onChange={set('precio_desde')} error={err('precio_desde')} />
            <Campo etiqueta="Precio hasta (CLP)" type="number" min="0" step="1000" value={f.precio_hasta} onChange={set('precio_hasta')} error={err('precio_hasta')} />
          </div>
        </>
      )}
      <section aria-labelledby="t-port-ficha" className="space-y-2">
        <h3 id="t-port-ficha" className="rotulo">Portafolio de la ficha</h3>
        <ul className="grid grid-cols-3 gap-2 sm:grid-cols-5">
          {f.portafolio.map((img, i) => (
            <li key={img.url + i} className="relative">
              <img src={img.url} alt={img.alt} className="aspect-square w-full object-cover" />
              <button type="button" className="boton-texto w-full justify-center" onClick={() => setF((x) => ({ ...x, portafolio: x.portafolio.filter((_, j) => j !== i) }))}>
                Quitar<span className="sr-only">: {img.alt}</span>
              </button>
            </li>
          ))}
        </ul>
        {f.portafolio.length < 20 && <SubirImagen etiqueta="Agregar trabajo al portafolio" onSubida={(img) => setF((x) => ({ ...x, portafolio: [...x.portafolio, img] }))} />}
      </section>
      <button className="boton-marca boton-grande">Guardar ficha</button>
    </form>
  )
}
