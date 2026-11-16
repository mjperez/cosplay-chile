import { Link } from 'react-router-dom'
import { EncabezadoPagina, useTitulo } from '../components/ui'

const SECCIONES = [
  {
    titulo: 'Qué datos pedimos y para qué',
    contenido: (
      <ul className="list-disc space-y-2 pl-6">
        <li><strong className="text-white">Correo y contraseña:</strong> para identificarte. La contraseña se guarda cifrada (hash argon2); nadie puede leerla.</li>
        <li><strong className="text-white">Nombre o apodo:</strong> para firmar tus publicaciones.</li>
        <li><strong className="text-white">Región:</strong> opcional, para mostrarte eventos y proveedores cercanos.</li>
        <li><strong className="text-white">Biografía, redes y portafolio:</strong> opcionales, solo si decides completarlos.</li>
      </ul>
    ),
  },
  {
    titulo: 'Tu perfil es privado por defecto',
    contenido: <p>Tu perfil solo aparece en el directorio público si tú lo activas, y puedes desactivarlo en cualquier momento desde Mi perfil.</p>,
  },
  {
    titulo: 'Tus derechos',
    contenido: (
      <p>
        Puedes acceder a tus datos y corregirlos desde <Link to="/perfil" className="enlace-claro">Mi perfil</Link>, y eliminar tu cuenta cuando quieras.
        Al eliminarla borramos tus datos personales; tus publicaciones en foros quedan firmadas como «Usuario eliminado» para no romper conversaciones ajenas.
      </p>
    ),
  },
  {
    titulo: 'Contacto',
    contenido: (
      <p>
        Para cualquier consulta sobre tus datos escríbenos desde el <Link to="/contacto" className="enlace-claro">formulario de contacto</Link>.
      </p>
    ),
  },
]

// RNF-11: finalidad declarada, consentimiento y derecho a supresión (Ley 21.719)
export default function Privacidad() {
  useTitulo('Privacidad')
  return (
    <article className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { texto: 'Privacidad' }]}
        titulo="Privacidad y tus datos"
        bajada="Cómo tratamos tus datos personales conforme a la Ley 21.719, con consentimiento explícito y derecho a supresión."
      />
      <div className="contenedor mt-10 max-w-3xl space-y-10 text-[16px] leading-relaxed text-tinta">
        {SECCIONES.map((s) => (
          <section key={s.titulo}>
            <h2 className="mb-3 font-display text-3xl font-bold text-white">{s.titulo}</h2>
            {s.contenido}
          </section>
        ))}
      </div>
    </article>
  )
}
