import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  DndContext, KeyboardSensor, PointerSensor, closestCenter,
  useSensor, useSensors,
} from '@dnd-kit/core'
import {
  SortableContext, arrayMove, sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'

import { mensajeDeError } from '../../api/cliente'
import { useEntidades, useReordenar, useSituaciones } from '../../api/consultas'
import FichaSituacion from './FichaSituacion'
import PanelSituacion from './PanelSituacion'
import FormularioSituacion from './FormularioSituacion'

export default function PaginaGaleria() {
  const { clave } = useParams()
  const [archivadas, setArchivadas] = useState(false)
  const [abierta, setAbierta] = useState(null)
  const [editando, setEditando] = useState(null)
  const [avisoOrden, setAvisoOrden] = useState(null)

  const { data: entidades = [] } = useEntidades()
  const entidad = entidades.find((e) => e.clave === clave)

  const { data: situaciones = [], isLoading, error } = useSituaciones(clave, archivadas)
  const reordenar = useReordenar(clave)

  const sensores = useSensors(
    // Un umbral de 6px evita que un clic se interprete como arrastre.
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const ids = useMemo(() => situaciones.map((s) => s.id), [situaciones])

  const alSoltar = ({ active, over }) => {
    if (!over || active.id === over.id) return
    const desde = ids.indexOf(active.id)
    const hasta = ids.indexOf(over.id)
    setAvisoOrden(null)
    reordenar.mutate(arrayMove(ids, desde, hasta), {
      onError: (fallo) => setAvisoOrden(mensajeDeError(fallo, 'No se pudo reordenar.')),
    })
  }

  if (error) return <div className="aviso aviso--error">{mensajeDeError(error)}</div>

  return (
    <>
      <p className="antetitulo">
        <Link to="/entidades" style={{ textDecoration: 'none' }}>Entidades</Link>
        {entidad?.region ? ` · ${entidad.region.nombre}` : ''}
      </p>
      <h1 className="titulo-pagina">{entidad?.nombre ?? clave}</h1>
      <p className="subtitulo">
        {archivadas
          ? 'Situaciones archivadas. Se conservan para consulta.'
          : 'Arrastra el numero para cambiar la prioridad. 1 es lo mas urgente.'}
      </p>

      <div className="barra-acciones">
        <button
          type="button"
          className={`chip${!archivadas ? ' chip--activo' : ''}`}
          onClick={() => setArchivadas(false)}
        >
          Activas
        </button>
        <button
          type="button"
          className={`chip${archivadas ? ' chip--activo' : ''}`}
          onClick={() => setArchivadas(true)}
        >
          Archivadas
        </button>

        <span className="barra-acciones__espacio" />

        <button
          type="button"
          className="boton boton--neutro"
          onClick={() => setEditando({})}
        >
          Nueva situacion
        </button>
        <Link to={`/entidades/${clave}/reporte`} className="boton boton--acento"
          style={{ textDecoration: 'none' }}>
          Generar Reporte Focos Rojos
        </Link>
      </div>

      {avisoOrden && <div className="aviso aviso--error">{avisoOrden}</div>}

      {isLoading && <p className="cargando">Cargando situaciones…</p>}

      {!isLoading && situaciones.length === 0 && (
        <div className="vacio">
          {archivadas
            ? 'No hay situaciones archivadas en esta entidad.'
            : 'Todavia no hay situaciones registradas. Comienza con la primera.'}
        </div>
      )}

      {!isLoading && situaciones.length > 0 && (
        <DndContext
          sensors={sensores}
          collisionDetection={closestCenter}
          onDragEnd={alSoltar}
        >
          <SortableContext items={ids} strategy={verticalListSortingStrategy}>
            <div style={{ display: 'grid', gap: 10 }}>
              {situaciones.map((s) => (
                <FichaSituacion
                  key={s.id}
                  situacion={s}
                  onAbrir={setAbierta}
                  arrastrable={!archivadas}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      {abierta && (
        <PanelSituacion
          situacionId={abierta.id}
          entidadClave={clave}
          onCerrar={() => setAbierta(null)}
          onEditar={(situacion) => { setAbierta(null); setEditando(situacion) }}
        />
      )}

      {editando && (
        <FormularioSituacion
          situacion={editando}
          entidadClave={clave}
          onCerrar={() => setEditando(null)}
        />
      )}
    </>
  )
}
