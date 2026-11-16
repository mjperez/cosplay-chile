import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import BotonReportar from '../../components/BotonReportar'
import CompartirRedes from '../../components/CompartirRedes'
import { CamposFotoCreditos, FiguraConCreditos, payloadFoto } from '../../components/FotoConCreditos'
import Icono from '../../components/diseno/Icono'
import useApi from '../../components/useApi'
import { Alerta, AreaTexto, Campo, Cargando, Migas, Vacio, useTitulo } from '../../components/ui'
import NoEncontrado from '../NoEncontrado'
import { nombreMes } from './Desafios'

function FormParticipar({ desafioId, onListo }) {
  const [titulo, setTitulo] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [foto, setFoto] = useState({ imagen: null, credito_fotografo: '', credito_cosplayer: '' })
  const [error, setError] = useState(null)
  const enviar = async (e) => {
    e.preventDefault()
    if (!foto.imagen) return setError({ message: 'Sube la foto de tu participación.' })
    try {
      await api(`/api/desafios/${desafioId}/participar`, { method: 'POST', body: { titulo, descripcion, ...payloadFoto(foto) } })
      onListo()
    } catch (err) {
      setError(err)
    }
  }
  return (
    <form id="participar" onSubmit={enviar} className="panel scroll-mt-6 space-y-5 p-6 sm:p-8" aria-labelledby="t-participar" noValidate>
      <h2 id="t-participar" className="font-display text-3xl font-bold text-white">Participa</h2>
      <Alerta tipo="error">{error?.message}</Alerta>
      <Campo etiqueta="Título de tu participación" requerido value={titulo} onChange={(e) => setTitulo(e.target.value)} error={error?.campos?.titulo} />
      <AreaTexto etiqueta="Cuéntanos cómo lo hiciste (opcional)" rows={3} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
      <CamposFotoCreditos valor={foto} onCambiar={setFoto} obligatoria errores={error?.campos} />
      <button className="boton-marca boton-grande">Enviar participación</button>
    </form>
  )
}

export default function DesafioDetalle() {
  const { id } = useParams()
  const { usuario } = useAuth()
  const location = useLocation()
  const { datos: d, error, cargando, recargar } = useApi(`/api/desafios/${id}`)
  useTitulo(d?.titulo || 'Desafío')
  if (cargando && !d) return <div className="contenedor"><Cargando /></div>
  if (error?.status === 404 || error?.status === 422) return <NoEncontrado titulo="Desafío no encontrado" />
  if (error) return <div className="contenedor py-10"><Alerta tipo="error">{error.message}</Alerta></div>
  if (!d) return null

  return (
    <div className="contenedor pb-24 pt-8 sm:pt-12">
      <Migas items={[{ texto: 'Inicio', a: '/' }, { texto: 'Desafíos', a: '/desafios' }, { texto: d.titulo }]} />
      <p className="sobretitulo first-letter:uppercase">{nombreMes(d.mes, d.anio)} · {d.abierto ? 'Abierto' : 'Cerrado'}</p>
      <h1 className="mt-3 max-w-4xl font-display text-[clamp(38px,5vw,68px)] leading-[1.05] font-bold text-white">{d.titulo}</h1>
      <p className="mt-4 max-w-3xl text-lg leading-relaxed text-lavanda">{d.descripcion}</p>
      {d.ganador && (
        <p className="mt-4 inline-flex items-center gap-2 rounded-full bg-estrella/15 px-4 py-2 text-sm font-bold text-estrella">
          <Icono nombre="trofeo" tamano={16} /> Ganó {d.ganador.nombre}
        </p>
      )}

      <div className="mt-8 max-w-3xl">
        {d.abierto && !usuario && (
          <Link to={`/ingresar?siguiente=${encodeURIComponent(location.pathname)}`} className="boton-marca boton-grande">Inicia sesión para participar</Link>
        )}
        {d.abierto && usuario && !d.ya_participo && <FormParticipar desafioId={d.id} onListo={recargar} />}
        {d.ya_participo && <Alerta tipo="exito">¡Ya estás participando en este desafío!</Alerta>}
      </div>

      <section className="mt-14" aria-labelledby="t-parts">
        <h2 id="t-parts" className="titulo-seccion mb-8">Participaciones ({d.participaciones})</h2>
        {d.lista_participaciones.length === 0 ? (
          <Vacio>Aún no hay participaciones. ¡Anímate!</Vacio>
        ) : (
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {d.lista_participaciones.map((p) => (
              <li key={p.id} className="flex flex-col gap-3">
                <div className="relative">
                  <FiguraConCreditos url={p.imagen_url} alt={p.imagen_alt} fotografo={p.credito_fotografo} cosplayer={p.credito_cosplayer} proporcion="aspect-[3/4]" />
                  {p.id === d.ganador_participacion_id && (
                    <span className="insignia absolute left-3 top-3 gap-1.5 bg-estrella text-[#2a1c00]">
                      <Icono nombre="trofeo" tamano={14} /> Ganadora
                    </span>
                  )}
                </div>
                <h3 className="font-display text-xl font-bold text-white">{p.titulo}</h3>
                <p className="text-sm text-lavanda">por {p.autor?.nombre || 'Usuario eliminado'}</p>
                {p.descripcion && <p className="text-sm text-tinta">{p.descripcion}</p>}
                <div className="flex items-center gap-3">
                  <CompartirRedes titulo={p.titulo} ruta={`/desafios/${d.id}`} />
                  <BotonReportar tipo="PARTICIPACION_DESAFIO" objetoId={p.id} compacto />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
