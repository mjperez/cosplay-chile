import 'leaflet/dist/leaflet.css'
import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'
import { Link } from 'react-router-dom'
import { useMeta } from '../../contexto/MetaContext'

const COLORES = { PROVEEDOR: '#ff7a6b', TIENDA: '#17e0ff', COMUNIDAD: '#8ef0b8' }

// RF-12: mapa interactivo de Chile con talleres, tiendas físicas y puntos de encuentro
export default function MapaChile({ puntos }) {
  const { etiqueta } = useMeta()
  return (
    <div>
      <ul className="mb-3 flex flex-wrap gap-4 text-sm text-lavanda" aria-label="Leyenda del mapa">
        {Object.entries(COLORES).map(([tipo, color]) => (
          <li key={tipo} className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-full" style={{ background: color }} aria-hidden="true" />
            {etiqueta('tipos_directorio', tipo)}
          </li>
        ))}
      </ul>
      <div
        className="h-[70vh] min-h-96 overflow-hidden rounded-panel border border-white/16"
        role="region"
        aria-label={`Mapa de Chile con ${puntos.length} lugares. La misma información está disponible en la vista de lista.`}
      >
        <MapContainer center={[-36.5, -71.5]} zoom={4} minZoom={3} scrollWheelZoom={false} className="h-full w-full">
          <TileLayer
            attribution='&copy; colaboradores de <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {puntos.map((p) => (
            <CircleMarker key={p.id} center={[p.lat, p.lng]} radius={9} pathOptions={{ color: '#0c0820', weight: 2, fillColor: COLORES[p.tipo], fillOpacity: 0.95 }}>
              <Popup>
                <strong>{p.nombre}</strong>
                <br />
                {etiqueta('tipos_directorio', p.tipo)} · {p.comuna ? `${p.comuna}, ` : ''}{etiqueta('regiones', p.region)}
                <br />
                <Link to={`/directorio/${p.id}`}>Ver ficha</Link>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}
