import { useEffect, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import Icono from '../../components/diseno/Icono'
import useApi from '../../components/useApi'
import { EncabezadoPagina, useTitulo } from '../../components/ui'
import { PESTANAS } from './pestanas'

const SEMANA = 7 * 24 * 3600 * 1000

function Contador({ icono, valor, texto }) {
  return (
    <div className="panel flex flex-[1_1_200px] items-center gap-4 px-5 py-4">
      <Icono nombre={icono} tamano={24} grosor={1.6} className="text-durazno" />
      <div>
        <dd className="font-display text-[34px] leading-none font-bold text-white">{valor ?? '—'}</dd>
        <dt className="mt-1 text-[13px] text-lavanda">{texto}</dt>
      </div>
    </div>
  )
}

// Panel del Administrador/Moderador (Fig. 10): navegación lateral con pestañas verticales (patrón ARIA tabs)
export default function Moderacion() {
  useTitulo('Panel de moderación')
  const [params, setParams] = useSearchParams()
  const activa = PESTANAS.find((p) => p.id === params.get('tab')) || PESTANAS[0]
  const refs = useRef({})
  const resumen = useApi('/api/moderacion/resumen')
  // Contadores que /resumen no trae: se calculan con los listados existentes
  const suspendidas = useApi('/api/moderacion/usuarios?estado=SUSPENDIDO')
  const resueltos = useApi('/api/moderacion/reportes?estado=RESUELTO')
  const descartados = useApi('/api/moderacion/reportes?estado=DESCARTADO')
  const { recargar: r1 } = resumen
  const { recargar: r2 } = suspendidas
  const { recargar: r3 } = resueltos
  const { recargar: r4 } = descartados
  useEffect(() => {
    r1()
    r2()
    r3()
    r4()
  }, [activa.id, r1, r2, r3, r4])

  const r = resumen.datos
  const ahora = Date.now()
  const resueltosSemana =
    resueltos.datos && descartados.datos
      ? [...resueltos.datos, ...descartados.datos].filter((x) => x.resuelto_at && ahora - new Date(x.resuelto_at).getTime() < SEMANA).length
      : undefined

  const ir = (id) => {
    setParams({ tab: id })
    refs.current[id]?.focus()
  }
  const alTeclado = (e, i) => {
    const n = PESTANAS.length
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') ir(PESTANAS[(i + 1) % n].id)
    else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') ir(PESTANAS[(i - 1 + n) % n].id)
    else if (e.key === 'Home') ir(PESTANAS[0].id)
    else if (e.key === 'End') ir(PESTANAS[n - 1].id)
    else return
    e.preventDefault()
  }

  const Panel = activa.Componente
  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { texto: 'Panel de moderación' }]}
        titulo="Panel de moderación"
        bajada="Solo para administradores. Revisión manual de tutoriales, reportes, mensajes y eventos antes de que lleguen a la comunidad."
      />
      <div className="contenedor mt-10">
        <dl className="flex flex-wrap gap-4" aria-label="Resumen">
          <Contador icono="lista" valor={r && r.contenidos_pendientes + r.eventos_pendientes} texto="Pendientes de revisión" />
          <Contador icono="bandera" valor={r?.reportes_abiertos} texto="Reportes abiertos" />
          <Contador icono="candado" valor={suspendidas.datos?.length} texto="Cuentas suspendidas" />
          <Contador icono="check" valor={resueltosSemana} texto="Reportes resueltos esta semana" />
        </dl>

        <div className="mt-8 grid grid-cols-1 items-start gap-6 lg:grid-cols-[15rem_minmax(0,1fr)]">
          <div className="flex min-w-0 flex-col gap-6">
            <div role="tablist" aria-label="Secciones de moderación" aria-orientation="vertical" className="flex gap-1 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible">
              {PESTANAS.map((p, i) => {
                const sel = p.id === activa.id
                const n = p.contador ? r?.[p.contador] : undefined
                return (
                  <button
                    key={p.id}
                    ref={(el) => (refs.current[p.id] = el)}
                    role="tab"
                    id={`tab-${p.id}`}
                    aria-selected={sel}
                    aria-controls={`panel-${p.id}`}
                    tabIndex={sel ? 0 : -1}
                    onClick={() => ir(p.id)}
                    onKeyDown={(e) => alTeclado(e, i)}
                    className={`flex min-h-11 flex-none items-center justify-between gap-3 whitespace-nowrap px-3 text-left text-sm lg:border-b lg:border-white/12 ${
                      sel ? 'bg-linear-120 from-coral to-fucsia font-bold text-tinta-oscura' : 'text-white hover:text-durazno'
                    }`}
                  >
                    {p.texto}
                    {n > 0 && (
                      <span className={`rounded-full px-2 text-xs font-bold ${sel ? 'bg-tinta-oscura/80 text-white' : 'bg-white/12 text-white'}`}>
                        {n}<span className="sr-only"> pendientes</span>
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
            <aside aria-labelledby="t-contenido-seg" className="panel hidden p-5 lg:block">
              <h2 id="t-contenido-seg" className="flex items-center gap-2 font-display text-lg font-bold text-white">
                <Icono nombre="escudo" tamano={18} className="text-durazno" /> Contenido de seguridad
              </h2>
              <p className="mt-2 text-[13px] text-lavanda">
                Los consejos de la página pública de Seguridad aún no se editan desde el panel (ver brechas del diseño).
              </p>
              <Link to="/seguridad#consejos" className="boton-contorno mt-4 w-full">Ver consejos publicados</Link>
            </aside>
          </div>

          <section role="tabpanel" id={`panel-${activa.id}`} aria-labelledby={`tab-${activa.id}`} tabIndex={0} className="min-w-0">
            <h2 className="mb-5 font-display text-[clamp(28px,3vw,38px)] font-bold text-white">{activa.texto}</h2>
            <Panel />
          </section>
        </div>
      </div>
    </div>
  )
}
