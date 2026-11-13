import { Navigate, Route, Routes } from 'react-router-dom'

import { AdminPagina } from './pages/AdminPagina'
import { ComunidadPagina } from './pages/ComunidadPagina'
import { ContenidoDetallePagina } from './pages/ContenidoDetallePagina'
import { ContenidoPagina } from './pages/ContenidoPagina'
import { DesafiosPagina } from './pages/DesafiosPagina'
import { DirectorioPagina } from './pages/DirectorioPagina'
import { EditorContenidoPagina } from './pages/EditorContenidoPagina'
import { EventoDetallePagina } from './pages/EventoDetallePagina'
import { EventosPagina } from './pages/EventosPagina'
import { ForoPagina } from './pages/ForoPagina'
import { InicioPagina } from './pages/InicioPagina'
import { IngresarPagina } from './pages/IngresarPagina'
import { NoEncontradaPagina } from './pages/NoEncontradaPagina'
import { PerfilPagina } from './pages/PerfilPagina'
import { PrivacidadPagina } from './pages/PrivacidadPagina'
import { RegistroPagina } from './pages/RegistroPagina'
import { TemaDetallePagina } from './pages/TemaDetallePagina'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<InicioPagina />} />
      <Route path="/directorio" element={<DirectorioPagina />} />
      <Route path="/contenido" element={<ContenidoPagina />} />
      <Route path="/contenido/nuevo" element={<EditorContenidoPagina />} />
      <Route path="/contenido/:id" element={<ContenidoDetallePagina />} />
      <Route path="/eventos" element={<EventosPagina />} />
      <Route path="/eventos/:id" element={<EventoDetallePagina />} />
      <Route path="/foro" element={<ForoPagina />} />
      <Route path="/foro/:id" element={<TemaDetallePagina />} />
      <Route path="/desafios" element={<DesafiosPagina />} />
      <Route path="/comunidad" element={<ComunidadPagina />} />
      <Route path="/perfil" element={<PerfilPagina />} />
      <Route path="/admin" element={<AdminPagina />} />
      <Route path="/ingresar" element={<IngresarPagina />} />
      <Route path="/registro" element={<RegistroPagina />} />
      <Route path="/privacidad" element={<PrivacidadPagina />} />
      <Route path="/inicio" element={<Navigate to="/" replace />} />
      <Route path="*" element={<NoEncontradaPagina />} />
    </Routes>
  )
}
