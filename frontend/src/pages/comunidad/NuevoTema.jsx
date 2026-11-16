import { useParams } from 'react-router-dom'
import useApi from '../../components/useApi'
import { EncabezadoPagina, useTitulo } from '../../components/ui'
import { FormNuevoTema } from './Comunidad'

// RF-23 crear temas; RF-27 foto con créditos; RF-29 historias de cómo llegaste al cosplay
export default function NuevoTema() {
  const { slug } = useParams()
  const { datos: foros } = useApi('/api/foros')
  const foro = foros?.find((f) => f.slug === slug)
  const esHistoria = slug === 'historias'
  useTitulo(esHistoria ? 'Contar mi historia' : 'Nuevo tema')

  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { a: '/comunidad', texto: 'Comunidad' }, { a: `/comunidad/${slug}`, texto: foro?.titulo || '…' }, { texto: 'Nuevo' }]}
        titulo={esHistoria ? 'Cuenta tu historia' : 'Crear un tema'}
        bajada={
          esHistoria
            ? '¿Cómo llegaste al cosplay? Tu experiencia puede animar a quienes recién empiezan.'
            : 'Recuerda las normas de la comunidad: respeto, sin acoso ni funas, y créditos en cada foto.'
        }
      />
      <div className="contenedor mt-10 max-w-3xl">
        <div className="panel p-6 sm:p-8">
          {foros && <FormNuevoTema foros={foros} foroInicial={slug} historia={esHistoria} />}
        </div>
      </div>
    </div>
  )
}
