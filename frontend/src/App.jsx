import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { RequiereAdmin, RequiereSesion } from './components/Protegida'
import Buscar from './pages/Buscar'
import Seguridad from './pages/seguridad/Seguridad'
import Favoritos from './pages/Favoritos'
import GuiaDetalle from './pages/guias/GuiaDetalle'
import Guias from './pages/guias/Guias'
import PublicarTutorial from './pages/guias/PublicarTutorial'
import Moderacion from './pages/moderacion/Moderacion'
import Calendario from './pages/calendario/Calendario'
import EventoDetalle from './pages/calendario/EventoDetalle'
import SugerirEvento from './pages/calendario/SugerirEvento'
import Directorio from './pages/directorio/Directorio'
import DirectorioDetalle from './pages/directorio/DirectorioDetalle'
import PerfilPublico from './pages/perfil/PerfilPublico'
import Comunidad from './pages/comunidad/Comunidad'
import ForoTemas from './pages/comunidad/ForoTemas'
import NuevoTema from './pages/comunidad/NuevoTema'
import TemaDetalle from './pages/comunidad/TemaDetalle'
import DesafioDetalle from './pages/desafios/DesafioDetalle'
import Desafios from './pages/desafios/Desafios'
import Inicio from './pages/Inicio'
import NoEncontrado from './pages/NoEncontrado'
import Privacidad from './pages/Privacidad'
import Acceso from './pages/auth/Acceso'
import Restablecer from './pages/auth/Restablecer'
import Perfil from './pages/perfil/Perfil'


export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Inicio />} />
        <Route path="ingresar" element={<Acceso modo="login" />} />
        <Route path="registro" element={<Acceso modo="registro" />} />
        <Route path="recuperar" element={<Acceso modo="recuperar" />} />
        <Route path="restablecer" element={<Restablecer />} />
        <Route path="buscar" element={<Buscar />} />
        <Route path="seguridad" element={<Seguridad />} />
        <Route path="contacto" element={<Seguridad pestanaInicial="contacto" />} />
        <Route path="privacidad" element={<Privacidad />} />
        <Route path="perfil" element={<RequiereSesion><Perfil /></RequiereSesion>} />
        <Route path="guias" element={<Guias />} />
        <Route path="guias/publicar" element={<RequiereSesion><PublicarTutorial /></RequiereSesion>} />
        <Route path="guias/:id" element={<GuiaDetalle />} />
        <Route path="favoritos" element={<RequiereSesion><Favoritos /></RequiereSesion>} />
        <Route path="moderacion" element={<RequiereAdmin><Moderacion /></RequiereAdmin>} />
        <Route path="directorio" element={<Directorio />} />
        <Route path="directorio/:id" element={<DirectorioDetalle />} />
        <Route path="personas/:id" element={<PerfilPublico />} />
        <Route path="calendario" element={<Calendario />} />
        <Route path="calendario/sugerir" element={<RequiereSesion><SugerirEvento /></RequiereSesion>} />
        <Route path="calendario/:id" element={<EventoDetalle />} />
        <Route path="comunidad" element={<Comunidad />} />
        <Route path="comunidad/temas/:id" element={<TemaDetalle />} />
        <Route path="comunidad/:slug" element={<ForoTemas />} />
        <Route path="comunidad/:slug/nuevo" element={<RequiereSesion><NuevoTema /></RequiereSesion>} />
        <Route path="desafios" element={<Desafios />} />
        <Route path="desafios/:id" element={<DesafioDetalle />} />
        <Route path="*" element={<NoEncontrado />} />
      </Route>
    </Routes>
  )
}
