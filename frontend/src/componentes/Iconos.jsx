/**
 * Iconos del menu lateral.
 *
 * El degradado se define UNA sola vez en `DefinicionDegradado`, que se monta al
 * inicio de la barra. Cada icono lo referencia por id: repetir la definicion en
 * cada SVG duplicaria identificadores y el navegador solo respetaria el primero.
 */

const trazo = {
  fill: 'none',
  stroke: 'url(#degradadoIcono)',
  strokeWidth: 1.7,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

export function DefinicionDegradado() {
  return (
    <svg width="0" height="0" aria-hidden="true" focusable="false"
      style={{ position: 'absolute' }}>
      <defs>
        <linearGradient id="degradadoIcono" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#D4AC4E" />
          <stop offset="55%" stopColor="#A57F2C" />
          <stop offset="100%" stopColor="#7FD4BE" />
        </linearGradient>
      </defs>
    </svg>
  )
}

function Base({ children }) {
  return (
    <svg className="barra__icono" viewBox="0 0 20 20" width="18" height="18"
      aria-hidden="true" focusable="false">
      {children}
    </svg>
  )
}

export const IconoEntidades = () => (
  <Base>
    <path {...trazo} d="M2.5 5.5 7 3.5l6 2 4.5-2v11l-4.5 2-6-2-4.5 2z" />
    <path {...trazo} d="M7 3.5v11M13 5.5v11" />
  </Base>
)

export const IconoPanorama = () => (
  <Base>
    <rect {...trazo} x="2.5" y="2.5" width="6" height="6" rx="1.4" />
    <rect {...trazo} x="11.5" y="2.5" width="6" height="6" rx="1.4" />
    <rect {...trazo} x="2.5" y="11.5" width="6" height="6" rx="1.4" />
    <rect {...trazo} x="11.5" y="11.5" width="6" height="6" rx="1.4" />
  </Base>
)

export const IconoConcentrado = () => (
  <Base>
    <rect {...trazo} x="2.5" y="3.5" width="15" height="13" rx="1.6" />
    <path {...trazo} d="M2.5 7.5h15M7.5 7.5v9M12.5 7.5v9" />
  </Base>
)

export const IconoUsuarios = () => (
  <Base>
    <circle {...trazo} cx="8" cy="7" r="2.8" />
    <path {...trazo} d="M2.8 16.5c0-2.9 2.3-4.8 5.2-4.8s5.2 1.9 5.2 4.8" />
    <path {...trazo} d="M14 4.6a2.6 2.6 0 0 1 0 5M15.4 12.2c1.4.6 2.3 1.9 2.3 3.6" />
  </Base>
)

export const IconoCategorias = () => (
  <Base>
    <path {...trazo} d="M3 3.5h6.2l7.8 7.8-6.2 6.2-7.8-7.8z" />
    <circle {...trazo} cx="7" cy="7" r="1.3" />
  </Base>
)

export const IconoAccesos = () => (
  <Base>
    <circle {...trazo} cx="10" cy="10" r="7.5" />
    <path {...trazo} d="M10 5.6V10l3 2" />
  </Base>
)
