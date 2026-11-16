import { useAuth } from '../../contexto/AuthContext'
import MiFicha from './MiFicha'
import MisEnvios from './MisEnvios'

// Secciones agregadas por fase: "Mis envíos" (Fase 2) y "Mi ficha del directorio" (Fase 3)
export default function SeccionesExtraPerfil() {
  const { usuario } = useAuth()
  return (
    <>
      {/* key: se recarga la ficha si cambian el tipo de perfil o el opt-in */}
      <MiFicha key={`${usuario.perfil?.tipo_perfil}-${usuario.perfil?.perfil_publico}`} />
      <MisEnvios />
    </>
  )
}
