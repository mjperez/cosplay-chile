import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { qs } from '../../api/client'
import { useAuth } from '../../contexto/AuthContext'
import { useMeta } from '../../contexto/MetaContext'
import BotonFavorito from '../../components/BotonFavorito'
import BotonReportar from '../../components/BotonReportar'
import Icono from '../../components/diseno/Icono'
import { COLOR_EVENTO, InsigniaEvento } from '../../components/diseno/Insignias'
import useApi from '../../components/useApi'
import useFavoritos from '../../components/useFavoritos'
import { Alerta, Cargando, EncabezadoPagina, GrupoChips, Vacio, useTitulo } from '../../components/ui'
import { REGION_CORTA } from '../directorio/MapaEsquematico'
import { FormSugerirEvento } from './SugerirEvento'

const DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
const DIAS_LARGOS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const nombreMes = (d) => d.toLocaleDateString('es-CL', { month: 'long' })
const capitalizar = (s) => s.charAt(0).toUpperCase() + s.slice(1)

function mesDesdeParam(valor) {
  const m = /^(\d{4})-(\d{2})$/.exec(valor || '')
  if (m) return new Date(Number(m[1]), Number(m[2]) - 1, 1)
  const h = new Date()
  return new Date(h.getFullYear(), h.getMonth(), 1)
}

const ocurreEl = (e, fecha) => e.fecha_inicio <= fecha && (e.fecha_fin || e.fecha_inicio) >= fecha

function Grilla({ mes, eventos, dia, onDia }) {
  const desplazamiento = (mes.getDay() + 6) % 7 // lunes = 0
  const diasMes = new Date(mes.getFullYear(), mes.getMonth() + 1, 0).getDate()
  const celdas = [...Array(desplazamiento).fill(null), ...Array.from({ length: diasMes }, (_, i) => i + 1)]
  while (celdas.length % 7) celdas.push(null)
  const hoy = iso(new Date())
  return (
    <div>
      <div aria-hidden="true" className="mb-2 grid grid-cols-7 gap-1.5 text-center text-[11px] font-bold uppercase tracking-[.12em] text-lavanda">
        {DIAS.map((d) => <span key={d}>{d}</span>)}
      </div>
      <ul className="grid grid-cols-7 gap-1.5" aria-label={`Días de ${nombreMes(mes)}`}>
        {celdas.map((n, k) => {
          if (!n) return <li key={k} aria-hidden="true" />
          const fecha = iso(new Date(mes.getFullYear(), mes.getMonth(), n))
          const evs = eventos.filter((e) => ocurreEl(e, fecha))
          const sel = dia === n
          const esHoy = fecha === hoy
          const etiqueta = `${DIAS_LARGOS[k % 7]} ${n} de ${nombreMes(mes)}${esHoy ? ' (hoy)' : ''}, ${
            evs.length ? `${evs.length} ${evs.length === 1 ? 'evento' : 'eventos'}` : 'sin eventos'
          }`
          return (
            <li key={k}>
              <button
                type="button"
                aria-pressed={sel}
                aria-label={etiqueta}
                onClick={() => onDia(sel ? 0 : n)}
                className={`flex aspect-square w-full flex-col items-start gap-1 overflow-hidden border p-1 text-left transition-colors sm:aspect-auto sm:min-h-[76px] sm:p-2 ${
                  sel ? 'border-coral bg-coral/22' : 'border-white/14 bg-white/5 hover:border-white/40'
                }`}
              >
                <span className={`font-display text-sm font-bold sm:text-lg ${esHoy ? 'rounded-full bg-cian px-1.5 text-tinta-oscura' : 'text-white'}`}>{n}</span>
                <span className="flex w-full flex-wrap gap-1" aria-hidden="true">
                  {evs.slice(0, 2).map((e) => (
                    <span key={e.id} className={`h-2 w-2 rounded-full sm:h-auto sm:w-full sm:truncate sm:px-1.5 sm:text-[10px] sm:font-bold sm:text-tinta-oscura ${COLOR_EVENTO[e.tipo]}`}>
                      <span className="hidden sm:inline">{e.nombre}</span>
                    </span>
                  ))}
                  {evs.length > 2 && <span className="text-[10px] text-lavanda">+{evs.length - 2}</span>}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function FilaEvento({ e, favorito }) {
  const { etiqueta } = useMeta()
  const inicio = new Date(`${e.fecha_inicio}T12:00:00`)
  return (
    <li className="flex gap-4 border border-white/14 bg-white/5 p-[18px]">
      <span aria-hidden="true" className="h-fit w-[58px] flex-none border border-white/50 py-1.5 text-center leading-[1.1]">
        <span className="block font-display text-2xl font-bold text-white">{inicio.getDate()}</span>
        <span className="block text-[11px] uppercase tracking-[.16em] text-durazno">{inicio.toLocaleDateString('es-CL', { month: 'short' }).replace('.', '')}</span>
      </span>
      <div className="min-w-0 flex-1">
        <InsigniaEvento tipo={e.tipo} />
        <h3 className="mt-2 font-display text-xl leading-tight font-bold">
          <Link to={`/calendario/${e.id}`} className="text-white no-underline hover:text-durazno">{e.nombre}</Link>
        </h3>
        <p className="mt-1 flex items-start gap-1.5 text-[13px] text-lavanda">
          <Icono nombre="ubicacion" tamano={14} className="mt-0.5" />
          <span>
            <span className="sr-only">
              {inicio.toLocaleDateString('es-CL', { weekday: 'long', day: 'numeric', month: 'long' })}
              {e.fecha_fin && e.fecha_fin !== e.fecha_inicio ? ` al ${new Date(`${e.fecha_fin}T12:00:00`).toLocaleDateString('es-CL', { day: 'numeric', month: 'long' })}` : ''}.{' '}
            </span>
            {e.lugar}{e.comuna ? `, ${e.comuna}` : ''}
            <span className="block">Región {REGION_CORTA[e.region] || etiqueta('regiones', e.region)}</span>
          </span>
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-x-5">
          {e.enlace_oficial && (
            <a href={e.enlace_oficial} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center gap-1.5 text-[13px] font-bold text-white underline underline-offset-[3px] hover:text-durazno">
              Sitio oficial y entradas <Icono nombre="externo" tamano={13} grosor={2.2} />
              <span className="sr-only"> de {e.nombre} (se abre en otra pestaña)</span>
            </a>
          )}
          <BotonReportar tipo="EVENTO" objetoId={e.id} compacto nombre={e.nombre} />
        </div>
      </div>
      <BotonFavorito variante="icono" tipo="EVENTO" objetoId={e.id} inicial={favorito} nombre={e.nombre} />
    </li>
  )
}

// RF-15, RF-16: calendario nacional de eventos cosplay
export default function Calendario() {
  useTitulo('Calendario de eventos')
  const { usuario } = useAuth()
  const { opciones, etiqueta } = useMeta()
  const esFavorito = useFavoritos()
  const [params, setParams] = useSearchParams()
  const mes = mesDesdeParam(params.get('mes'))
  const tipo = params.get('tipo') || ''
  const region = params.get('region') || ''
  const [dia, setDia] = useState(0)

  const desde = iso(mes)
  const hasta = iso(new Date(mes.getFullYear(), mes.getMonth() + 1, 0))
  // Se pide el mes completo por tipo; la región se filtra aquí para ofrecer solo regiones con eventos
  const { datos, error, cargando } = useApi(`/api/eventos${qs({ tipo, desde, hasta, por_pagina: 100 })}`)
  const delMes = datos?.items || []
  const eventos = region ? delMes.filter((e) => e.region === region) : delMes
  const regiones = [...new Set([...delMes.map((e) => e.region), ...(region ? [region] : [])])]

  const cambiar = (cambios) => {
    const p = new URLSearchParams(params)
    for (const [k, v] of Object.entries(cambios)) {
      if (v) p.set(k, v)
      else p.delete(k)
    }
    setParams(p)
    setDia(0)
  }
  const moverMes = (delta) => {
    const m = new Date(mes.getFullYear(), mes.getMonth() + delta, 1)
    cambiar({ mes: `${m.getFullYear()}-${String(m.getMonth() + 1).padStart(2, '0')}` })
  }

  const fechaDia = dia ? iso(new Date(mes.getFullYear(), mes.getMonth(), dia)) : ''
  const lista = (dia ? eventos.filter((e) => ocurreEl(e, fechaDia)) : eventos).slice().sort((a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio))
  const titulo = `${capitalizar(nombreMes(mes))} ${mes.getFullYear()}`

  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { texto: 'Calendario' }]}
        titulo="Calendario nacional de eventos"
        bajada="Convenciones, concursos, meetups y talleres de todo Chile, con enlace a la organización oficial. No vendemos entradas: te llevamos directo a la boletería oficial."
      />

      <div className="contenedor mt-10">
        <div className="panel flex flex-col gap-4 p-5 sm:px-6">
          <GrupoChips etiqueta="Tipo" valor={tipo} onCambiar={(v) => cambiar({ tipo: v })} opciones={[{ valor: '', texto: 'Todos' }, ...opciones('tipos_evento')]} />
          <GrupoChips
            etiqueta="Región"
            valor={region}
            onCambiar={(v) => cambiar({ region: v })}
            opciones={[{ valor: '', texto: 'Todas' }, ...regiones.map((r) => ({ valor: r, texto: REGION_CORTA[r] || etiqueta('regiones', r) }))]}
          />
        </div>

        <div className="mt-6 grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
          <section aria-labelledby="t-mes" className="panel p-4 sm:p-6">
            <div className="mb-5 flex items-center justify-between gap-3">
              <button type="button" className="boton-icono" onClick={() => moverMes(-1)} aria-label="Mes anterior">
                <Icono nombre="izquierda" tamano={18} grosor={2.2} />
              </button>
              <h2 id="t-mes" className="font-display text-[clamp(24px,2.6vw,34px)] font-bold text-white" aria-live="polite">{titulo}</h2>
              <button type="button" className="boton-icono" onClick={() => moverMes(1)} aria-label="Mes siguiente">
                <Icono nombre="derecha" tamano={18} grosor={2.2} />
              </button>
            </div>
            {cargando && <Cargando />}
            <Alerta tipo="error">{error?.message}</Alerta>
            <Grilla mes={mes} eventos={eventos} dia={dia} onDia={setDia} />
            <ul className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-[13px] text-lavanda" aria-label="Colores por tipo de evento">
              {opciones('tipos_evento').map((o) => (
                <li key={o.valor} className="flex items-center gap-2">
                  <span aria-hidden="true" className={`size-2.5 rounded-full ${COLOR_EVENTO[o.valor]}`} /> {o.texto}
                </li>
              ))}
            </ul>
          </section>

          <section aria-labelledby="t-lista">
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
              <h2 id="t-lista" className="font-display text-[28px] font-bold text-white">
                {dia ? `Eventos del ${dia} de ${nombreMes(mes)}` : `Eventos de ${nombreMes(mes)}`}
              </h2>
              <p role="status" className="text-sm text-lavanda">
                {lista.length === 1 ? '1 evento' : `${lista.length} eventos`}
              </p>
            </div>
            {dia > 0 && (
              <button type="button" className="boton-contorno mb-4" onClick={() => setDia(0)}>Ver todo el mes</button>
            )}
            {datos && lista.length === 0 ? (
              <Vacio>
                No hay eventos con esos filtros. ¿Conoces uno? <a href="#sugerir" className="enlace-claro">Súmalo con el formulario de más abajo</a>.
              </Vacio>
            ) : (
              <ul className="space-y-3">
                {lista.map((e) => <FilaEvento key={e.id} e={e} favorito={esFavorito('EVENTO', e.id)} />)}
              </ul>
            )}
          </section>
        </div>
      </div>

      <section id="sugerir" aria-labelledby="t-sugerir" className="contenedor mt-20 scroll-mt-6">
        <div className="grid gap-10 border border-white/12 bg-[rgba(22,12,52,.94)] p-6 sm:p-10 lg:grid-cols-[1fr_1.6fr]">
          <div>
            <h2 id="t-sugerir" className="font-display text-[clamp(28px,3vw,40px)] leading-tight font-bold text-white">Sugiere un evento o reporta un cambio</h2>
            <p className="mt-4 text-[15px] leading-relaxed text-lavanda">
              Organizadores y usuarios pueden proponer eventos nuevos o avisar de cambios. Es necesario iniciar sesión para mantener la trazabilidad
              de cada sugerencia; el equipo la revisa antes de publicarla.
            </p>
            <p className="mt-4 inline-flex items-center gap-2 text-sm text-durazno">
              <Icono nombre="reloj" tamano={16} /> Un evento sugerido queda pendiente de revisión
            </p>
          </div>
          <div>
            {usuario ? (
              <FormSugerirEvento />
            ) : (
              <div className="flex h-full flex-col items-start justify-center gap-4">
                <p className="text-[15px] text-lavanda">Inicia sesión para enviar una sugerencia.</p>
                <Link to="/ingresar?siguiente=%2Fcalendario%23sugerir" className="boton-marca boton-grande">Ingresar para sugerir</Link>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
