import { useEffect } from 'react'

/** Panel lateral. Se cierra con Escape o haciendo clic fuera. */
export default function Panel({ titulo, onCerrar, children, acciones }) {
  useEffect(() => {
    const alPresionar = (evento) => {
      if (evento.key === 'Escape') onCerrar()
    }
    document.addEventListener('keydown', alPresionar)
    return () => document.removeEventListener('keydown', alPresionar)
  }, [onCerrar])

  return (
    <div
      className="panel-fondo"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onCerrar() }}
    >
      <aside className="panel" role="dialog" aria-modal="true" aria-label={titulo}>
        <header className="panel__encabezado">
          <h2 className="panel__titulo">{titulo}</h2>
          <button type="button" className="boton boton--texto" onClick={onCerrar}>
            Cerrar
          </button>
        </header>
        {children}
        {acciones && <div className="barra-acciones" style={{ marginTop: 22 }}>{acciones}</div>}
      </aside>
    </div>
  )
}
