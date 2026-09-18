import { ESTATUS } from '../utilidades/formato'

export function DistintivoEstatus({ estatus }) {
  const config = ESTATUS[estatus] ?? { etiqueta: estatus, clase: '' }
  return <span className={`distintivo ${config.clase}`}>{config.etiqueta}</span>
}

export function DistintivoCategoria({ nombre }) {
  return <span className="distintivo distintivo--categoria">{nombre}</span>
}
