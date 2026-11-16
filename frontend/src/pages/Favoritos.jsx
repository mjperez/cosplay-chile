import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import Icono from '../components/diseno/Icono'
import useApi from '../components/useApi'
import { Alerta, Cargando, EncabezadoPagina, Vacio, useTitulo } from '../components/ui'

export const GRUPOS_FAVORITOS = [
  { tipo: 'CONTENIDO', titulo: 'Guías' },
  { tipo: 'DIRECTORIO', titulo: 'Proveedores' },
  { tipo: 'EVENTO', titulo: 'Eventos' },
]

// Lista de favoritos de un tipo, con botón para quitar (RF-25). La usan /favoritos y el perfil.
export function ListaFavoritos({ items, onQuitar }) {
  if (!items.length) return <p className="py-4 text-sm text-lavanda">No tienes favoritos de este tipo.</p>
  return (
    <ul>
      {items.map((f) => (
        <li key={f.id} className="flex items-center gap-4 border-b border-white/12 py-3">
          {f.imagen_url ? (
            <img src={f.imagen_url} alt="" className="size-12 flex-none object-cover" />
          ) : (
            <span aria-hidden="true" className="size-12 flex-none bg-linear-135 from-ciruela to-uva" />
          )}
          <div className="min-w-0 flex-1">
            <Link to={f.enlace} className="font-bold text-white no-underline hover:text-durazno">{f.titulo}</Link>
            {f.subtitulo && <p className="truncate text-[13px] text-lavanda">{f.subtitulo}</p>}
          </div>
          <button type="button" className="boton-icono border-coral text-coral" onClick={() => onQuitar(f)} aria-label={`Quitar ${f.titulo} de favoritos`}>
            <Icono nombre="corazon" tamano={17} relleno="currentColor" />
          </button>
        </li>
      ))}
    </ul>
  )
}

export function useListaFavoritos() {
  const r = useApi('/api/favoritos')
  const [aviso, setAviso] = useState('')
  const quitar = async (f) => {
    try {
      await api(`/api/favoritos/${f.tipo}/${f.objeto_id}`, { method: 'DELETE' })
      setAviso(`Quitaste «${f.titulo}» de tus favoritos.`)
      r.recargar()
    } catch (e) {
      setAviso(e.message)
    }
  }
  return { ...r, aviso, quitar }
}

// RF-25
export default function Favoritos() {
  useTitulo('Mis favoritos')
  const { datos, error, cargando, aviso, quitar } = useListaFavoritos()
  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { a: '/perfil', texto: 'Mi perfil' }, { texto: 'Favoritos' }]}
        titulo="Mis favoritos"
        bajada="Las guías, proveedores y eventos que guardaste."
      />
      <div className="contenedor mt-10 max-w-4xl">
        <Alerta tipo="info" className="mb-4">{aviso}</Alerta>
        {cargando && <Cargando />}
        <Alerta tipo="error">{error?.message}</Alerta>
        {datos && datos.length === 0 && (
          <Vacio>Aún no guardas favoritos. Usa el corazón en guías, fichas del directorio y eventos.</Vacio>
        )}
        {datos && datos.length > 0 &&
          GRUPOS_FAVORITOS.map((g) => {
            const items = datos.filter((f) => f.tipo === g.tipo)
            if (!items.length) return null
            return (
              <section key={g.tipo} className="panel mb-6 p-6" aria-labelledby={`fav-${g.tipo}`}>
                <h2 id={`fav-${g.tipo}`} className="font-display text-2xl font-bold text-white">{g.titulo}</h2>
                <ListaFavoritos items={items} onQuitar={quitar} />
              </section>
            )
          })}
      </div>
    </div>
  )
}
