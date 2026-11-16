import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { Alerta, Campo, EncabezadoPagina, useTitulo } from '../../components/ui'

export default function Restablecer() {
  useTitulo('Nueva contraseña')
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [confirmacion, setConfirmacion] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState(null)

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    if (password !== confirmacion) {
      setError({ message: 'Las contraseñas no coinciden.', campos: { confirmacion: 'Debe ser igual a la nueva contraseña' } })
      return
    }
    try {
      const r = await api('/api/auth/restablecer', { method: 'POST', body: { token, password } })
      setMensaje(r.mensaje)
    } catch (err) {
      setError(err)
    }
  }

  return (
    <div className="pb-24">
      <EncabezadoPagina migas={[{ a: '/', texto: 'Inicio' }, { a: '/ingresar', texto: 'Tu cuenta' }, { texto: 'Nueva contraseña' }]} titulo="Crea una nueva contraseña" />
      <div className="contenedor mt-10 max-w-xl">
        <div className="panel space-y-5 p-6 sm:p-8">
          {!token ? (
            <Alerta tipo="error">
              El enlace está incompleto. <Link to="/recuperar" className="enlace-claro">Solicita uno nuevo</Link>.
            </Alerta>
          ) : mensaje ? (
            <Alerta tipo="exito">
              {mensaje} <Link to="/ingresar" className="enlace-claro">Ingresar</Link>
            </Alerta>
          ) : (
            <>
              <Alerta tipo="error">{error?.message}</Alerta>
              <form onSubmit={enviar} className="space-y-5" noValidate>
                <Campo etiqueta="Nueva contraseña" type="password" autoComplete="new-password" requerido value={password}
                  onChange={(e) => setPassword(e.target.value)} error={error?.campos?.password} ayuda="Mínimo 8 caracteres, con letras y números." />
                <Campo etiqueta="Repite la contraseña" type="password" autoComplete="new-password" requerido value={confirmacion}
                  onChange={(e) => setConfirmacion(e.target.value)} error={error?.campos?.confirmacion} />
                <button className="boton-marca boton-grande w-full">Guardar contraseña</button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
