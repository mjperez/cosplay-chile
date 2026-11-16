import { Link } from 'react-router-dom'
import { useTitulo } from '../components/ui'

export default function NoEncontrado({ titulo = 'Página no encontrada', texto = 'La página que buscas no existe o fue movida.' }) {
  useTitulo(titulo)
  return (
    <div className="mx-auto max-w-lg px-gutter py-20 text-center">
      <p aria-hidden="true" className="font-display text-7xl font-extrabold text-durazno">404</p>
      <h1 className="mt-2 font-display text-4xl font-bold">{titulo}</h1>
      <p className="texto-suave mt-3">{texto}</p>
      <Link to="/" className="boton-marca mt-8">Volver al inicio</Link>
    </div>
  )
}
