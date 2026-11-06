import { Navigate, Route, Routes } from 'react-router-dom'

import { ContenidoDetallePagina } from './pages/ContenidoDetallePagina'
import { ContenidoPagina } from './pages/ContenidoPagina'
import { DirectorioPagina } from './pages/DirectorioPagina'
import { EditorContenidoPagina } from './pages/EditorContenidoPagina'
import { InicioPagina } from './pages/InicioPagina'
import { IngresarPagina } from './pages/IngresarPagina'
import { NoEncontradaPagina } from './pages/NoEncontradaPagina'
import { PrivacidadPagina } from './pages/PrivacidadPagina'
import { RegistroPagina } from './pages/RegistroPagina'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<InicioPagina />} />
      <Route path="/directorio" element={<DirectorioPagina />} />
      <Route path="/contenido" element={<ContenidoPagina />} />
      <Route path="/contenido/nuevo" element={<EditorContenidoPagina />} />
      <Route path="/contenido/:id" element={<ContenidoDetallePagina />} />
      <Route path="/ingresar" element={<IngresarPagina />} />
      <Route path="/registro" element={<RegistroPagina />} />
      <Route path="/privacidad" element={<PrivacidadPagina />} />
      <Route path="/inicio" element={<Navigate to="/" replace />} />
      <Route path="*" element={<NoEncontradaPagina />} />
    </Routes>
  )
}
