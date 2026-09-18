import { mensajeDeError } from '../../api/cliente'
import { useBitacora, useCambiarArchivado, useSituacion } from '../../api/consultas'
import Panel from '../../componentes/Panel'
import { DistintivoCategoria, DistintivoEstatus } from '../../componentes/Distintivo'
import { fechaCorta, fechaHora } from '../../utilidades/formato'

function Dato({ etiqueta, children }) {
  if (!children) return null
  return (
    <div style={{ marginBottom: 16 }}>
      <div className="campo__etiqueta">{etiqueta}</div>
      <div style={{ fontSize: 14, lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{children}</div>
    </div>
  )
}

function Bitacora({ movimientos }) {
  if (!movimientos?.length) return <p className="cargando">Sin movimientos.</p>

  return (
    <div className="bitacora">
      {movimientos.map((m) => (
        <div key={m.id} className="bitacora__item">
          <div className="bitacora__cabeza">
            {m.accion_etiqueta}
            {m.campo_etiqueta ? `: ${m.campo_etiqueta}` : ''}
          </div>
          <div className="bitacora__fecha">{fechaHora(m.creado_en)} · {m.usuario_nombre}</div>
          {(m.valor_anterior || m.valor_nuevo) && (
            <div className="bitacora__cambio">
              {m.valor_anterior && <span className="bitacora__antes">{m.valor_anterior}</span>}
              {m.valor_anterior && m.valor_nuevo && ' → '}
              {m.valor_nuevo && <span className="bitacora__despues">{m.valor_nuevo}</span>}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default function PanelSituacion({ situacionId, entidadClave, onCerrar, onEditar }) {
  const { data: situacion, isLoading, error } = useSituacion(situacionId)
  const { data: movimientos } = useBitacora(situacionId)
  const cambiarArchivado = useCambiarArchivado(entidadClave)

  const archivar = (accion) => {
    cambiarArchivado.mutate({ id: situacionId, accion }, { onSuccess: onCerrar })
  }

  return (
    <Panel
      titulo={situacion?.tema ?? 'Situacion'}
      onCerrar={onCerrar}
      acciones={
        situacion && (
          <>
            <button type="button" className="boton boton--primario"
              onClick={() => onEditar(situacion)}>
              Editar
            </button>
            {situacion.archivada ? (
              <button type="button" className="boton boton--neutro"
                onClick={() => archivar('reabrir')} disabled={cambiarArchivado.isPending}>
                Reabrir
              </button>
            ) : (
              <button type="button" className="boton boton--neutro"
                onClick={() => archivar('cerrar')} disabled={cambiarArchivado.isPending}>
                Cerrar y archivar
              </button>
            )}
          </>
        )
      }
    >
      {isLoading && <p className="cargando">Cargando…</p>}
      {error && <div className="aviso aviso--error">{mensajeDeError(error)}</div>}

      {situacion && (
        <>
          <div className="ficha__pie" style={{ marginTop: 0, marginBottom: 20 }}>
            <DistintivoEstatus estatus={situacion.estatus} />
            <DistintivoCategoria nombre={situacion.categoria_nombre} />
            {!situacion.archivada && (
              <span className="tarjeta__meta">Prioridad {situacion.orden}</span>
            )}
          </div>

          <Dato etiqueta="Estatus actual">{situacion.estatus_detalle}</Dato>
          <Dato etiqueta="Acciones que se estan realizando">{situacion.acciones}</Dato>
          <Dato etiqueta="Fecha de inicio">{fechaCorta(situacion.fecha_inicio)}</Dato>
          <Dato etiqueta="Responsable">{situacion.responsable}</Dato>
          <Dato etiqueta="Fecha estimada de solucion">
            {fechaCorta(situacion.fecha_estimada_solucion)}
          </Dato>

          <h3 style={{ fontSize: 15, color: 'var(--verde-d)', margin: '26px 0 10px' }}>
            Bitacora de cambios
          </h3>
          <Bitacora movimientos={movimientos} />
        </>
      )}
    </Panel>
  )
}
