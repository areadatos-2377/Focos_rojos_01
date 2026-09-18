import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { DistintivoCategoria, DistintivoEstatus } from '../../componentes/Distintivo'
import { fechaCorta } from '../../utilidades/formato'

/**
 * Ficha arrastrable de la galeria.
 *
 * El asa de arrastre es solo el numero de orden, no la ficha entera: asi se puede
 * hacer clic en el tema para abrir el detalle sin que el gesto se confunda con un
 * arrastre. `@dnd-kit` aporta ademas el manejo por teclado.
 */
export default function FichaSituacion({ situacion, onAbrir, arrastrable = true }) {
  const {
    attributes, listeners, setNodeRef, transform, transition, isDragging,
  } = useSortable({ id: situacion.id, disabled: !arrastrable })

  const estilo = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 5 : undefined,
  }

  const resumen = (situacion.estatus_detalle || '').trim()

  return (
    <article
      ref={setNodeRef}
      style={estilo}
      className={`ficha${isDragging ? ' ficha--arrastrando' : ''}`}
    >
      <div
        className={`ficha__orden${situacion.orden === 1 ? ' ficha__orden--top' : ''}`}
        title={arrastrable ? 'Arrastra para cambiar la prioridad' : 'Archivada'}
        {...(arrastrable ? { ...attributes, ...listeners } : {})}
      >
        {situacion.orden ?? '–'}
      </div>

      <div>
        <button type="button" className="ficha__tema" onClick={() => onAbrir(situacion)}>
          {situacion.tema}
        </button>
        {resumen && (
          <p className="ficha__detalle">
            {resumen.length > 150 ? `${resumen.slice(0, 150)}…` : resumen}
          </p>
        )}
        <div className="ficha__pie">
          <DistintivoEstatus estatus={situacion.estatus} />
          <DistintivoCategoria nombre={situacion.categoria_nombre} />
          <span className="tarjeta__meta">
            Inicio {fechaCorta(situacion.fecha_inicio)}
            {situacion.fecha_estimada_solucion
              && ` · Estimada ${fechaCorta(situacion.fecha_estimada_solucion)}`}
          </span>
        </div>
      </div>

      <div className="tarjeta__meta" style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
        {situacion.responsable}
      </div>
    </article>
  )
}
