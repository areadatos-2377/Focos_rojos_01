export const ESTATUS = {
  ABIERTA: { etiqueta: 'Abierta', clase: 'distintivo--abierta' },
  EN_PROCESO: { etiqueta: 'En proceso', clase: 'distintivo--proceso' },
  CERRADA: { etiqueta: 'Cerrada', clase: 'distintivo--cerrada' },
}

export const ROLES = {
  REGIONAL: 'Regional',
  ADMINISTRADOR: 'Administrador',
  SUPER_ADMIN: 'Super administrador',
}

/** Convierte '2026-05-02' a '02/05/2026' sin que la zona horaria reste un dia. */
export const fechaCorta = (iso) => {
  if (!iso) return ''
  const [anio, mes, dia] = iso.slice(0, 10).split('-')
  return `${dia}/${mes}/${anio}`
}

export const fechaHora = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleString('es-MX', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

/** Agrupa entidades por region, conservando el orden alfabetico de la region. */
export const agruparPorRegion = (entidades = []) => {
  const grupos = new Map()
  for (const entidad of entidades) {
    const clave = entidad.region?.nombre ?? 'Sin region'
    if (!grupos.has(clave)) grupos.set(clave, [])
    grupos.get(clave).push(entidad)
  }
  return [...grupos.entries()].sort(([a], [b]) => a.localeCompare(b, 'es'))
}
