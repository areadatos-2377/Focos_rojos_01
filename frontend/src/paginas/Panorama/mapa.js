/**
 * Mapa de mosaico de Mexico.
 *
 * Cada entidad ocupa una pieza del mismo tamano, colocada en su posicion
 * geografica aproximada. Se prefiere a un mapa por area porque las 24 entidades
 * pesan lo mismo en el reporte: en un mapa real, Sonora dominaria la lectura
 * frente a Tlaxcala aunque tuviera menos focos rojos.
 *
 * Los ocho estados que no operan con IMSS-Bienestar simplemente no aparecen.
 */

export const COLUMNAS = 9
export const FILAS = 6

// clave -> { fila, columna, sigla }
export const CUADRICULA = {
  'baja-california': { fila: 0, columna: 0, sigla: 'BC' },
  sonora: { fila: 0, columna: 1, sigla: 'SON' },
  tamaulipas: { fila: 0, columna: 5, sigla: 'TAM' },

  'baja-california-sur': { fila: 1, columna: 0, sigla: 'BCS' },
  sinaloa: { fila: 1, columna: 1, sigla: 'SIN' },
  zacatecas: { fila: 1, columna: 3, sigla: 'ZAC' },
  'san-luis-potosi': { fila: 1, columna: 4, sigla: 'SLP' },

  nayarit: { fila: 2, columna: 1, sigla: 'NAY' },
  hidalgo: { fila: 2, columna: 5, sigla: 'HGO' },
  veracruz: { fila: 2, columna: 6, sigla: 'VER' },

  colima: { fila: 3, columna: 2, sigla: 'COL' },
  michoacan: { fila: 3, columna: 3, sigla: 'MIC' },
  'estado-de-mexico': { fila: 3, columna: 4, sigla: 'MEX' },
  'ciudad-de-mexico': { fila: 3, columna: 5, sigla: 'CMX' },
  tlaxcala: { fila: 3, columna: 6, sigla: 'TLX' },
  puebla: { fila: 3, columna: 7, sigla: 'PUE' },

  guerrero: { fila: 4, columna: 3, sigla: 'GRO' },
  morelos: { fila: 4, columna: 4, sigla: 'MOR' },
  oaxaca: { fila: 4, columna: 5, sigla: 'OAX' },
  tabasco: { fila: 4, columna: 6, sigla: 'TAB' },
  campeche: { fila: 4, columna: 7, sigla: 'CAM' },
  yucatan: { fila: 4, columna: 8, sigla: 'YUC' },

  chiapas: { fila: 5, columna: 5, sigla: 'CHP' },
  'quintana-roo': { fila: 5, columna: 8, sigla: 'ROO' },
}

/**
 * Rampa secuencial de un solo tono, derivada del verde institucional.
 * Validada con el script de la guia de visualizacion: luminosidad monotona,
 * separacion suficiente entre pasos contiguos, tono unico y el paso mas claro
 * por encima del minimo de contraste contra el fondo blanco.
 */
export const RAMPA = ['#8FBDB0', '#5E9A8B', '#3A7768', '#1E5B4F']

/** Los dos pasos oscuros piden tinta blanca; los claros, tinta oscura. */
export const TINTA = ['#161A1D', '#161A1D', '#FFFFFF', '#FFFFFF']

export const SIN_DATOS = '#F1EFE9'
export const TINTA_SIN_DATOS = '#98989A'

/**
 * Reparte 1..max en los cuatro pasos de la rampa. Devuelve -1 para el cero,
 * que se pinta con el tono neutro: "ninguno" no es el extremo claro de una
 * escala de magnitud, es una categoria aparte.
 */
export function escalon(valor, maximo) {
  if (!valor) return -1
  if (maximo <= 1) return RAMPA.length - 1
  const ancho = maximo / RAMPA.length
  return Math.min(RAMPA.length - 1, Math.floor((valor - 0.0001) / ancho))
}

/** Rangos de cada escalon, para la leyenda. */
export function rangosLeyenda(maximo) {
  if (maximo <= 0) return []
  const ancho = maximo / RAMPA.length
  return RAMPA.map((color, i) => {
    const desde = Math.floor(i * ancho) + 1
    const hasta = Math.round((i + 1) * ancho)
    return {
      color,
      etiqueta: desde >= hasta ? `${hasta}` : `${desde}–${hasta}`,
    }
  }).filter((r, i, todos) => todos.findIndex((x) => x.etiqueta === r.etiqueta) === i)
}
