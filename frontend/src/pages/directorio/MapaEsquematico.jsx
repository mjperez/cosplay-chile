import { useMeta } from '../../contexto/MetaContext'
import IconoBase from '../../components/diseno/Icono'

// Nombres cortos para las etiquetas del mapa
export const REGION_CORTA = {
  AP: 'Arica', TA: 'Tarapacá', AN: 'Antofagasta', AT: 'Atacama', CO: 'Coquimbo', VA: 'Valparaíso', RM: 'Metropolitana',
  LI: "O'Higgins", ML: 'Maule', NB: 'Ñuble', BI: 'Biobío', AR: 'Araucanía', LR: 'Los Ríos', LL: 'Los Lagos', AI: 'Aysén', MA: 'Magallanes',
}

// Mapa esquemático de Chile (diseño): cada región con lugares es un botón que filtra el listado.
// La posición vertical se calcula desde la latitud media de los puntos reales de /api/directorio/mapa.
const NORTE = -17.5
const SUR = -55
const ALTO = 460

// Silueta estilizada del país (no es cartográfica)
const SILUETA =
  'M40 4 L50 6 L48 40 L54 70 L50 110 L56 150 L52 190 L58 230 L54 270 L60 300 L56 330 L62 360 L70 390 L84 420 L80 440 L92 456 L56 456 L46 440 L50 420 L36 400 L42 380 L30 360 L36 330 L28 300 L32 270 L26 230 L32 190 L26 150 L32 110 L28 70 L34 40 Z'

export function regionesDesdePuntos(puntos = []) {
  const acc = {}
  for (const p of puntos) {
    if (!p.region) continue
    const r = (acc[p.region] ||= { suma: 0, n: 0 })
    r.suma += p.lat
    r.n += 1
  }
  return Object.entries(acc)
    .map(([region, r]) => ({ region, lat: r.suma / r.n, lugares: r.n }))
    .sort((a, b) => b.lat - a.lat)
}

export default function MapaEsquematico({ puntos, region, onRegion, onDetallado }) {
  const { etiqueta } = useMeta()
  const regiones = regionesDesdePuntos(puntos)
  const y = (lat) => Math.min(ALTO - 12, Math.max(12, ((NORTE - lat) / (NORTE - SUR)) * ALTO))

  return (
    <aside aria-labelledby="t-mapa-esq" className="panel p-5">
      <h2 id="t-mapa-esq" className="flex items-center gap-2 font-display text-xl font-bold text-white">
        <IconoBase nombre="ubicacion" tamano={20} className="text-durazno" /> Mapa de Chile
      </h2>
      <p className="mt-1.5 text-[13px] leading-snug text-lavanda">
        <span className="hidden lg:inline">Toca una región para ver talleres, tiendas y grupos cerca de ti. Mapa esquemático.</span>
        <span className="lg:hidden">Filtra por región con los botones de abajo o abre el mapa detallado.</span>
      </p>
      {/* En móvil la silueta se oculta: las mismas regiones están como chips en los filtros */}
      <div className="relative mx-auto mt-4 hidden lg:block" style={{ height: ALTO, width: '100%', maxWidth: 230 }}>
        <svg viewBox={`0 0 120 ${ALTO}`} preserveAspectRatio="none" aria-hidden="true" className="absolute left-1/2 top-0 h-full w-[60px] -translate-x-1/2">
          <defs>
            <linearGradient id="chile-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#7a2cff" />
              <stop offset="1" stopColor="#c2456a" />
            </linearGradient>
          </defs>
          <path d={SILUETA} fill="url(#chile-grad)" stroke="#17e0ff" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
        </svg>
        <ul>
          {regiones.map((r, i) => {
            const activa = region === r.region
            const izquierda = i % 2 === 1
            return (
              <li key={r.region} className="absolute left-1/2" style={{ top: y(r.lat), transform: 'translateY(-50%)' }}>
                <button
                  type="button"
                  aria-pressed={activa}
                  aria-label={`Filtrar por región ${etiqueta('regiones', r.region)} (${r.lugares} ${r.lugares === 1 ? 'lugar' : 'lugares'})`}
                  onClick={() => onRegion(activa ? '' : r.region)}
                  className={`absolute top-1/2 flex min-h-8 -translate-y-1/2 items-center gap-1.5 whitespace-nowrap text-xs ${
                    izquierda ? 'right-[-6px] flex-row-reverse' : 'left-[-6px]'
                  } ${activa ? 'font-bold text-white' : 'text-lavanda hover:text-white'}`}
                >
                  <span
                    aria-hidden="true"
                    className={`flex-none rounded-full ${activa ? 'size-[18px] bg-coral shadow-[0_0_0_5px_rgba(255,122,107,.35)]' : 'size-3 bg-cian shadow-[0_0_0_3px_rgba(23,224,255,.3)]'}`}
                  />
                  {REGION_CORTA[r.region] || etiqueta('regiones', r.region)}
                </button>
              </li>
            )
          })}
        </ul>
      </div>
      <p className="mt-4 hidden items-start gap-2 text-[13px] text-lavanda lg:flex">
        <span aria-hidden="true" className="text-cian">✓</span> Talleres, tiendas físicas y puntos de encuentro
      </p>
      {onDetallado && (
        <button type="button" onClick={onDetallado} className="boton-contorno mt-4 w-full">
          Ver mapa detallado
        </button>
      )}
    </aside>
  )
}

