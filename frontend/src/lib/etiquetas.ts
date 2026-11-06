/** Etiquetas y tonos del directorio, compartidos entre panel y tarjeta. */

export const ETIQUETAS_TIPO: Record<string, string> = {
  cosmaker: 'Cosmaker',
  sastre: 'Sastrería',
  fotografo: 'Fotografía',
  tienda: 'Tienda',
  organizador: 'Organizador de eventos',
  otro: 'Otro oficio',
}

export const TONO_POR_TIPO: Record<string, 'marca' | 'acento' | 'neutro' | 'exito'> = {
  tienda: 'acento',
  cosmaker: 'marca',
  sastre: 'marca',
  organizador: 'exito',
  fotografo: 'neutro',
  otro: 'neutro',
}
