import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { qs } from '../api/client'
import { useMeta } from '../contexto/MetaContext'
import Icono from '../components/diseno/Icono'
import useApi from '../components/useApi'
import { Alerta, Campo, Cargando, Casilla, EncabezadoPagina, Selector, Vacio, useTitulo } from '../components/ui'

const GRUPOS = [
  { tipo: 'guia', titulo: 'Guías y tutoriales', icono: 'libro', mas: (q) => `/guias?q=${q}` },
  { tipo: 'proveedor', titulo: 'Profesionales', icono: 'tienda', mas: (q) => `/directorio?tipo=PROVEEDOR&q=${q}` },
  { tipo: 'tienda', titulo: 'Tiendas', icono: 'tienda', mas: (q) => `/directorio?tipo=TIENDA&q=${q}` },
  { tipo: 'comunidad', titulo: 'Comunidades', icono: 'personas', mas: (q) => `/directorio?tipo=COMUNIDAD&q=${q}` },
  { tipo: 'tema', titulo: 'Hilos del foro', icono: 'chat', mas: () => '/comunidad' },
  { tipo: 'evento', titulo: 'Eventos', icono: 'calendario', mas: () => '/calendario' },
]

// RF-31: búsqueda unificada con filtros (Fig. 4: Búsqueda Global «extend» Aplicar filtros)
export default function Buscar() {
  const { opciones } = useMeta()
  const [params, setParams] = useSearchParams()
  const q = params.get('q') || ''
  const tipos = params.get('tipos') ? params.get('tipos').split(',') : []
  const region = params.get('region') || ''
  const nivel = params.get('nivel') || ''
  const categoria = params.get('categoria') || ''
  const [texto, setTexto] = useState(q)
  useTitulo(q ? `Resultados para «${q}»` : 'Buscar')
  const { datos: categorias } = useApi('/api/categorias')
  const { datos, error, cargando } = useApi(
    q.length >= 2 ? `/api/busqueda${qs({ q, tipos: tipos.join(','), region, nivel, categoria, limite: 10 })}` : null,
  )

  const cambiar = (campo, valor) => {
    const p = new URLSearchParams(params)
    if (valor) p.set(campo, valor)
    else p.delete(campo)
    setParams(p)
  }
  const alternarTipo = (t) => {
    // Sin filtro = todos marcados; al desmarcar uno se parte de la lista completa
    const base = tipos.length ? tipos : GRUPOS.map((g) => g.tipo)
    const nuevos = base.includes(t) ? base.filter((x) => x !== t) : [...base, t]
    cambiar('tipos', nuevos.length === GRUPOS.length ? '' : nuevos.join(','))
  }
  useEffect(() => setTexto(q), [q])
  const buscar = (e) => {
    e.preventDefault()
    cambiar('q', texto.trim())
  }

  return (
    <div className="pb-24">
      <EncabezadoPagina
        migas={[{ a: '/', texto: 'Inicio' }, { texto: 'Buscar' }]}
        titulo="Buscar"
        bajada="Busca por palabras clave en guías, profesionales, tiendas, hilos del foro y eventos. Las tildes no importan: prueba «EVA», «maquillaje» o «Santiago»."
      />
      <div className="contenedor mt-10 grid gap-6 lg:grid-cols-[19rem_1fr]">
        <aside aria-label="Filtros de búsqueda">
          <form onSubmit={buscar} className="panel space-y-5 p-5">
            <Campo etiqueta="Palabras clave" type="search" value={texto} onChange={(e) => setTexto(e.target.value)} minLength={2} />
            <button className="boton-marca w-full">Buscar</button>
            <fieldset>
              <legend className="sobretitulo mb-3">Buscar en</legend>
              <div className="space-y-2">
                {GRUPOS.map((g) => (
                  <Casilla key={g.tipo} etiqueta={g.titulo} checked={tipos.length === 0 || tipos.includes(g.tipo)} onChange={() => alternarTipo(g.tipo)} />
                ))}
              </div>
            </fieldset>
            <Selector etiqueta="Región (directorio y eventos)" vacio="Todo Chile" opciones={opciones('regiones')} value={region} onChange={(e) => cambiar('region', e.target.value)} />
            <Selector
              etiqueta="Categoría de guías"
              vacio="Todas"
              opciones={(categorias || []).map((c) => ({ valor: c.slug, texto: c.nombre }))}
              value={categoria}
              onChange={(e) => cambiar('categoria', e.target.value)}
            />
            <Selector etiqueta="Nivel de guías" vacio="Todos" opciones={opciones('niveles')} value={nivel} onChange={(e) => cambiar('nivel', e.target.value)} />
          </form>
        </aside>
        <div>
          {!q && <Vacio>Escribe al menos 2 letras para buscar.</Vacio>}
          {cargando && <Cargando texto="Buscando…" />}
          <Alerta tipo="error">{error?.message}</Alerta>
          {datos && (
            <>
              <p role="status" className="mb-6 text-lavanda">
                {datos.total === 0 ? (
                  `No encontramos resultados para «${q}».`
                ) : (
                  <>
                    <strong className="text-white">{datos.total} resultados</strong> para «{q}»
                  </>
                )}
              </p>
              {GRUPOS.filter((g) => datos.grupos[g.tipo]?.length).map((g) => (
                <section key={g.tipo} className="panel mb-6 px-5 pb-2 pt-5" aria-labelledby={`r-${g.tipo}`}>
                  <div className="mb-1 flex items-center justify-between gap-3">
                    <h2 id={`r-${g.tipo}`} className="flex items-center gap-2.5 font-display text-xl font-bold text-white">
                      <Icono nombre={g.icono} tamano={20} className="text-durazno" />
                      {g.titulo} <span className="font-sans text-sm font-normal text-lavanda">({datos.grupos[g.tipo].length})</span>
                    </h2>
                    <Link to={g.mas(encodeURIComponent(q))} className="enlace-claro text-sm">
                      Ver sección<span className="sr-only">: {g.titulo}</span>
                    </Link>
                  </div>
                  <ul>
                    {datos.grupos[g.tipo].map((r) => (
                      <li key={r.id} className="border-t border-white/12 first:border-t-0">
                        <Link to={r.enlace} className="group flex min-h-11 items-center justify-between gap-3 py-3 text-white no-underline">
                          <span>
                            <span className="block font-bold group-hover:text-durazno">{r.titulo}</span>
                            {r.subtitulo && <span className="block text-sm text-lavanda">{r.subtitulo}</span>}
                          </span>
                          <Icono nombre="derecha" tamano={16} className="text-durazno" />
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
              {datos.total === 0 && <Vacio>Prueba con otra palabra, quita filtros o revisa la ortografía. Las tildes no importan.</Vacio>}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
