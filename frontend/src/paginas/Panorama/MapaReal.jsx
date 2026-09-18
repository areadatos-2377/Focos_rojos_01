import { TRAZOS, VIEWBOX } from './geometria'
import { RAMPA, SIN_DATOS, escalon } from './mapa'

/** Estados sin operacion de IMSS-Bienestar: se dibujan apagados y sin interaccion. */
const FUERA = '#F4F2ED'
const BORDE = '#FFFFFF'

/**
 * Mapa geografico de Mexico.
 *
 * Los trazos vienen precalculados en `geometria.js`, generado por
 * `scripts/generar_mapa.py`. Aqui no hay proyeccion ni libreria de mapas: son
 * `<path>` pintados segun la magnitud.
 */
export default function MapaReal({
  porClave, metrica, maximo, onEncima, onSalir, onElegir,
}) {
  return (
    <svg
      className="mapa"
      viewBox={VIEWBOX}
      role="img"
      aria-label="Mapa de Mexico por numero de situaciones"
    >
      {/* Primero los estados fuera del sistema, para que los activos queden encima
          y su contorno no se corte. */}
      {Object.entries(TRAZOS)
        .filter(([clave]) => !porClave.has(clave))
        .map(([clave, d]) => (
          <path key={clave} d={d} fill={FUERA} stroke={BORDE} strokeWidth="1.2" />
        ))}

      {Object.entries(TRAZOS)
        .filter(([clave]) => porClave.has(clave))
        .map(([clave, d]) => {
          const entidad = porClave.get(clave)
          const valor = entidad[metrica] ?? 0
          const paso = escalon(valor, maximo)

          return (
            <path
              key={clave}
              className="mapa__estado"
              d={d}
              fill={paso < 0 ? SIN_DATOS : RAMPA[paso]}
              stroke={BORDE}
              strokeWidth="1.2"
              tabIndex={0}
              role="button"
              aria-label={`${entidad.nombre}: ${valor}`}
              onMouseEnter={() => onEncima(entidad)}
              onMouseLeave={onSalir}
              onFocus={() => onEncima(entidad)}
              onBlur={onSalir}
              onClick={() => onElegir(clave)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onElegir(clave)
                }
              }}
            />
          )
        })}
    </svg>
  )
}
