import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { PanelFiltros } from '../components/directorio/PanelFiltros'
import { TarjetaProveedor } from '../components/directorio/TarjetaProveedor'
import { Disposicion } from '../components/layout/Disposicion'
import { Boton } from '../components/ui/Boton'
import {
  api,
  type OpcionesDirectorio,
  type PaginaProveedores,
} from '../lib/api'

const POR_PAGINA = 9

export function DirectorioPagina() {
  const [parametros, setParametros] = useSearchParams()
  const [opciones, setOpciones] = useState<OpcionesDirectorio | null>(null)
  const [resultado, setResultado] = useState<{
    clave: string
    datos: PaginaProveedores
  } | null>(null)
  const [error, setError] = useState('')

  const q = parametros.get('q') ?? ''
  const region = parametros.get('region') ?? ''
  const tipo = parametros.get('tipo') ?? ''
  const sinRegion = parametros.get('sin_region') === '1'
  const pagina = Math.max(1, Number(parametros.get('pagina') ?? '1') || 1)

  // La consulta al backend se arma como cadena. La cadena es la clave del
  // efecto: dos renders con los mismos filtros producen el mismo texto y no
  // se vuelve a pedir lo mismo.
  const consulta = useMemo(() => {
    const nueva = new URLSearchParams()
    if (q) nueva.set('q', q)
    if (region) nueva.set('region', region)
    if (tipo) nueva.set('tipo', tipo)
    if (sinRegion) nueva.set('sin_region', 'true')
    nueva.set('limite', String(POR_PAGINA))
    nueva.set('desplazamiento', String((pagina - 1) * POR_PAGINA))
    return nueva.toString()
  }, [q, region, tipo, sinRegion, pagina])

  useEffect(() => {
    let vigente = true
    api
      .proveedores(consulta)
      .then((datos) => {
        if (!vigente) return
        setResultado({ clave: consulta, datos })
        setError('')
      })
      .catch(() => {
        if (vigente) setError('No pudimos cargar el directorio. Revisa tu conexión.')
      })
    return () => {
      vigente = false
    }
  }, [consulta])

  useEffect(() => {
    let vigente = true
    api
      .opcionesDirectorio()
      .then((datos) => {
        if (vigente) setOpciones(datos)
      })
      .catch(() => {
        // Sin opciones el panel muestra solo «Todas»: el listado sigue usable.
      })
    return () => {
      vigente = false
    }
  }, [])

  // Cargando se deriva del resultado, no de un estado aparte: si la clave no
  // coincide con la de los datos en pantalla, todavía hay una petición en vuelo.
  const cargando = resultado?.clave !== consulta
  const datos = resultado?.datos

  function cambiarFiltros(cambios: Record<string, string | null>) {
    const siguiente = new URLSearchParams(parametros)
    for (const [clave, valor] of Object.entries(cambios)) {
      if (valor === null || valor === '') siguiente.delete(clave)
      else siguiente.set(clave, valor)
    }
    // Cualquier cambio de filtro vuelve a la primera página: si no, se pide
    // una página que puede no existir con el nuevo conjunto de resultados.
    siguiente.delete('pagina')
    setParametros(siguiente)
  }

  function irAPagina(numero: number) {
    const siguiente = new URLSearchParams(parametros)
    if (numero <= 1) siguiente.delete('pagina')
    else siguiente.set('pagina', String(numero))
    setParametros(siguiente)
  }

  const totalPaginas = datos ? Math.max(1, Math.ceil(datos.total / POR_PAGINA)) : 1
  const hayFiltros = Boolean(q || region || tipo || sinRegion)

  return (
    <Disposicion>
      <div className="mx-auto max-w-6xl px-4 py-12">
        <header className="max-w-2xl">
          <h1 className="text-3xl font-black tracking-tight text-tinta-900">
            Directorio
          </h1>
          <p className="mt-3 text-base text-tinta-600">
            Cosmakers, sastres, tiendas y organizadores de la comunidad cosplay
            chilena. Filtra por región o por tipo de servicio.
          </p>
        </header>

        <div className="mt-8">
          <PanelFiltros
            q={q}
            region={region}
            tipo={tipo}
            sinRegion={sinRegion}
            opciones={opciones}
            onCambio={cambiarFiltros}
            onLimpiar={() => setParametros(new URLSearchParams())}
            hayFiltros={hayFiltros}
          />
        </div>

        <p aria-live="polite" className="mt-6 text-sm text-tinta-600">
          {cargando
            ? 'Cargando fichas…'
            : datos
              ? datos.total === 1
                ? '1 ficha encontrada'
                : `${datos.total} fichas encontradas`
              : ''}
        </p>

        {error && (
          <p role="alert" className="mt-4 rounded-control bg-error-50 px-3 py-2 text-sm text-error-600">
            {error}
          </p>
        )}

        {!cargando && datos && datos.total === 0 && (
          <div className="mt-8 rounded-tarjeta border border-dashed border-tinta-300 bg-white px-6 py-16 text-center">
            <p className="text-base font-semibold text-tinta-900">
              No hay fichas con esos filtros
            </p>
            <p className="mx-auto mt-2 max-w-md text-sm text-tinta-600">
              Prueba con otra región o con otro tipo de servicio. También puedes
              quitar los filtros y ver el directorio completo.
            </p>
            {hayFiltros && (
              <div className="mt-6 flex justify-center">
                <Boton variante="secundario" onClick={() => setParametros(new URLSearchParams())}>
                  Quitar los filtros
                </Boton>
              </div>
            )}
          </div>
        )}

        {datos && datos.total > 0 && (
          <>
            <ul className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {datos.elementos.map((proveedor) => (
                <li key={proveedor.id_proveedor} className="h-full">
                  <TarjetaProveedor proveedor={proveedor} />
                </li>
              ))}
            </ul>

            {totalPaginas > 1 && (
              <nav
                aria-label="Paginación del directorio"
                className="mt-10 flex items-center justify-between gap-4"
              >
                <Boton
                  variante="secundario"
                  onClick={() => irAPagina(pagina - 1)}
                  disabled={pagina <= 1}
                >
                  Anterior
                </Boton>
                <p className="text-sm text-tinta-600">
                  Página {pagina} de {totalPaginas}
                </p>
                <Boton
                  variante="secundario"
                  onClick={() => irAPagina(pagina + 1)}
                  disabled={pagina >= totalPaginas}
                >
                  Siguiente
                </Boton>
              </nav>
            )}
          </>
        )}
      </div>
    </Disposicion>
  )
}
