import { useState } from 'react'
import { mensajeDeError } from '../../api/cliente'
import { useGuardarSituacion } from '../../api/consultas'
import Panel from '../../componentes/Panel'
import SelectorCategoria from '../../componentes/SelectorCategoria'

const VACIO = {
  categoria: null,
  tema: '',
  fecha_inicio: '',
  estatus: 'ABIERTA',
  estatus_detalle: '',
  acciones: '',
  responsable: '',
  fecha_estimada_solucion: '',
}

/** Los 6 campos del formato institucional, mas el estatus como catalogo. */
export default function FormularioSituacion({ situacion, entidadClave, onCerrar }) {
  const esNueva = !situacion?.id
  const guardar = useGuardarSituacion(entidadClave)
  const [errores, setErrores] = useState({})
  const [fallo, setFallo] = useState(null)

  const [datos, setDatos] = useState({
    ...VACIO,
    ...situacion,
    categoria: situacion?.categoria ?? null,
    fecha_estimada_solucion: situacion?.fecha_estimada_solucion ?? '',
  })

  const cambiar = (campo) => (evento) =>
    setDatos((previos) => ({ ...previos, [campo]: evento.target.value }))

  const validar = () => {
    const nuevos = {}
    if (!datos.categoria) nuevos.categoria = 'Elige una categoria.'
    if (datos.tema.trim().length < 5) nuevos.tema = 'Describe el tema (al menos 5 caracteres).'
    if (!datos.fecha_inicio) nuevos.fecha_inicio = 'Indica la fecha de inicio.'
    if (!datos.estatus_detalle.trim()) nuevos.estatus_detalle = 'Describe el estatus actual.'
    if (!datos.acciones.trim()) nuevos.acciones = 'Indica que se esta haciendo.'
    if (!datos.responsable.trim()) nuevos.responsable = 'Indica el responsable.'
    setErrores(nuevos)
    return Object.keys(nuevos).length === 0
  }

  const enviar = async (evento) => {
    evento.preventDefault()
    setFallo(null)
    if (!validar()) return

    const cuerpo = {
      categoria: datos.categoria,
      tema: datos.tema.trim(),
      fecha_inicio: datos.fecha_inicio,
      estatus: datos.estatus,
      estatus_detalle: datos.estatus_detalle.trim(),
      acciones: datos.acciones.trim(),
      responsable: datos.responsable.trim(),
      fecha_estimada_solucion: datos.fecha_estimada_solucion || null,
    }
    // La entidad se fija al crear y no se puede mover despues.
    if (esNueva) cuerpo.entidad = entidadClave

    try {
      await guardar.mutateAsync(esNueva ? cuerpo : { id: situacion.id, ...cuerpo })
      onCerrar()
    } catch (error) {
      setFallo(mensajeDeError(error, 'No se pudo guardar la situacion.'))
    }
  }

  return (
    <Panel titulo={esNueva ? 'Nueva situacion' : 'Editar situacion'} onCerrar={onCerrar}>
      <form onSubmit={enviar}>
        {fallo && <div className="aviso aviso--error">{fallo}</div>}

        <SelectorCategoria
          valor={datos.categoria}
          onCambio={(id) => setDatos((p) => ({ ...p, categoria: id }))}
          error={errores.categoria}
        />

        <div className="campo">
          <label className="campo__etiqueta" htmlFor="tema">Tema</label>
          <input id="tema" className="campo__control" value={datos.tema}
            onChange={cambiar('tema')} />
          {errores.tema && <p className="campo__error">{errores.tema}</p>}
        </div>

        <div className="campo__fila">
          <div className="campo">
            <label className="campo__etiqueta" htmlFor="fecha_inicio">Fecha de inicio</label>
            <input id="fecha_inicio" type="date" className="campo__control"
              value={datos.fecha_inicio} onChange={cambiar('fecha_inicio')} />
            {errores.fecha_inicio && <p className="campo__error">{errores.fecha_inicio}</p>}
          </div>

          <div className="campo">
            <label className="campo__etiqueta" htmlFor="estatus">Estatus</label>
            <select id="estatus" className="campo__control" value={datos.estatus}
              onChange={cambiar('estatus')}>
              <option value="ABIERTA">Abierta</option>
              <option value="EN_PROCESO">En proceso</option>
            </select>
            <p className="tarjeta__meta">
              Para cerrarla usa el boton del panel de detalle: ahi se archiva y se
              reacomoda la prioridad del resto.
            </p>
          </div>
        </div>

        <div className="campo">
          <label className="campo__etiqueta" htmlFor="estatus_detalle">Estatus actual</label>
          <textarea id="estatus_detalle" className="campo__control"
            value={datos.estatus_detalle} onChange={cambiar('estatus_detalle')} />
          {errores.estatus_detalle && <p className="campo__error">{errores.estatus_detalle}</p>}
        </div>

        <div className="campo">
          <label className="campo__etiqueta" htmlFor="acciones">
            Acciones que se estan realizando para solventarlo
          </label>
          <textarea id="acciones" className="campo__control" value={datos.acciones}
            onChange={cambiar('acciones')} />
          {errores.acciones && <p className="campo__error">{errores.acciones}</p>}
        </div>

        <div className="campo__fila">
          <div className="campo">
            <label className="campo__etiqueta" htmlFor="responsable">Responsable</label>
            <input id="responsable" className="campo__control" value={datos.responsable}
              onChange={cambiar('responsable')} placeholder="Nombre libre" />
            {errores.responsable && <p className="campo__error">{errores.responsable}</p>}
          </div>

          <div className="campo">
            <label className="campo__etiqueta" htmlFor="fecha_estimada">
              Fecha estimada de solucion
            </label>
            <input id="fecha_estimada" type="date" className="campo__control"
              value={datos.fecha_estimada_solucion || ''}
              onChange={cambiar('fecha_estimada_solucion')} />
            <p className="tarjeta__meta">Opcional.</p>
          </div>
        </div>

        <div className="barra-acciones" style={{ marginTop: 20 }}>
          <button type="submit" className="boton boton--primario" disabled={guardar.isPending}>
            {guardar.isPending ? 'Guardando…' : 'Guardar'}
          </button>
          <button type="button" className="boton boton--texto" onClick={onCerrar}>
            Cancelar
          </button>
        </div>
      </form>
    </Panel>
  )
}
