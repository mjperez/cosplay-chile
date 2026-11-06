/** Etiquetas del contenido editorial, compartidas entre lista, detalle y editor. */

export const ETIQUETAS_CONTENIDO: Record<string, string> = {
  guia: 'Guía',
  entrevista: 'Entrevista',
  articulo: 'Artículo',
}

export const ETIQUETAS_NIVEL: Record<string, string> = {
  basico: 'Básico',
  intermedio: 'Intermedio',
  avanzado: 'Avanzado',
}

export const TONO_CONTENIDO: Record<string, 'marca' | 'acento' | 'neutro' | 'exito'> = {
  guia: 'marca',
  entrevista: 'acento',
  articulo: 'neutro',
}
