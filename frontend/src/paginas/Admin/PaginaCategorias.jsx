import { useState } from 'react'
import { mensajeDeError } from '../../api/cliente'
import {
  useCategorias, useEliminarCategoria, useFusionarCategorias, useRenombrarCategoria,
} from '../../api/consultas'
import { useAuth } from '../../contextos/AuthContext'
import Panel from '../../componentes/Panel'

function PanelFusion({ categoria, categorias, onCerrar }) {
  const fusionar = useFusionarCategorias()
  const [destino, setDestino] = useState('')
  const [fallo, setFallo] = useState(null)
  const [resultado, setResultado] = useState(null)

  const confirmar = async () => {
    setFallo(null)
    try {
      const datos = await fusionar.mutateAsync({ id: categoria.id, destino: Number(destino) })
      setResultado(datos)
    } catch (error) {
      setFallo(mensajeDeError(error, 'No se pudo fusionar.'))
    }
  }

  return (
    <Panel titulo={`Fusionar "${categoria.nombre}"`} onCerrar={onCerrar}>
      {fallo && <div className="aviso aviso--error">{fallo}</div>}

      {resultado ? (
        <>
          <div className="aviso aviso--info">
            {resultado.detalle} Se movieron {resultado.situaciones_movidas} situaciones.
          </div>
          <button type="button" className="boton boton--primario" onClick={onCerrar}>
            Listo
          </button>
        </>
      ) : (
        <>
          <p style={{ fontSize: 14, lineHeight: 1.55 }}>
            Todas las situaciones que hoy usan <strong>{categoria.nombre}</strong> pasaran
            a la categoria que elijas, y <strong>{categoria.nombre}</strong> dejara de
            aparecer en la lista.
          </p>
          <p className="tarjeta__meta">
            La bitacora conserva el nombre con que se registro cada cambio, asi que el
            historial sigue siendo legible.
          </p>

          <div className="campo">
            <label className="campo__etiqueta" htmlFor="destino">Categoria de destino</label>
            <select id="destino" className="campo__control" value={destino}
              onChange={(e) => setDestino(e.target.value)}>
              <option value="">Selecciona…</option>
              {categorias
                .filter((c) => c.id !== categoria.id)
                .map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
          </div>

          <div className="barra-acciones">
            <button type="button" className="boton boton--primario"
              onClick={confirmar} disabled={!destino || fusionar.isPending}>
              {fusionar.isPending ? 'Fusionando…' : 'Fusionar'}
            </button>
            <button type="button" className="boton boton--texto" onClick={onCerrar}>
              Cancelar
            </button>
          </div>
        </>
      )}
    </Panel>
  )
}

export default function PaginaCategorias() {
  const { esSuperAdmin } = useAuth()
  const { data: categorias = [], isLoading, error } = useCategorias()
  const renombrar = useRenombrarCategoria()
  const eliminar = useEliminarCategoria()

  const [editando, setEditando] = useState(null)
  const [nombre, setNombre] = useState('')
  const [fusionando, setFusionando] = useState(null)
  const [aviso, setAviso] = useState(null)

  const comenzarEdicion = (categoria) => {
    setEditando(categoria.id)
    setNombre(categoria.nombre)
    setAviso(null)
  }

  const guardar = async (categoria) => {
    try {
      await renombrar.mutateAsync({ id: categoria.id, nombre: nombre.trim() })
      setEditando(null)
    } catch (fallo) {
      setAviso(mensajeDeError(fallo, 'No se pudo renombrar.'))
    }
  }

  const borrar = async (categoria) => {
    setAviso(null)
    try {
      await eliminar.mutateAsync(categoria.id)
    } catch (fallo) {
      setAviso(mensajeDeError(fallo, 'No se pudo eliminar.'))
    }
  }

  if (error) return <div className="aviso aviso--error">{mensajeDeError(error)}</div>

  return (
    <>
      <p className="antetitulo">Administracion</p>
      <h1 className="titulo-pagina">Categorias</h1>
      <p className="subtitulo">
        Catalogo compartido. Cualquier usuario puede agregar una categoria al registrar
        una situacion; aqui se ordenan para que no crezca sin control.
      </p>

      {aviso && <div className="aviso aviso--error">{aviso}</div>}

      {isLoading && <p className="cargando">Cargando categorias…</p>}

      <div style={{ display: 'grid', gap: 8 }}>
        {categorias.map((c) => (
          <article key={c.id} className="ficha" style={{ gridTemplateColumns: '1fr auto' }}>
            {editando === c.id ? (
              <input className="campo__control" value={nombre} autoFocus
                onChange={(e) => setNombre(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') guardar(c)
                  if (e.key === 'Escape') setEditando(null)
                }} />
            ) : (
              <div style={{ fontWeight: 600, fontSize: 15, alignSelf: 'center' }}>
                {c.nombre}
              </div>
            )}

            {esSuperAdmin && (
              <div style={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                {editando === c.id ? (
                  <>
                    <button type="button" className="boton boton--primario"
                      onClick={() => guardar(c)} disabled={nombre.trim().length < 3}>
                      Guardar
                    </button>
                    <button type="button" className="boton boton--texto"
                      onClick={() => setEditando(null)}>
                      Cancelar
                    </button>
                  </>
                ) : (
                  <>
                    <button type="button" className="boton boton--texto"
                      onClick={() => comenzarEdicion(c)}>
                      Renombrar
                    </button>
                    <button type="button" className="boton boton--texto"
                      onClick={() => setFusionando(c)}>
                      Fusionar
                    </button>
                    <button type="button" className="boton boton--texto"
                      onClick={() => borrar(c)} disabled={eliminar.isPending}>
                      Eliminar
                    </button>
                  </>
                )}
              </div>
            )}
          </article>
        ))}
      </div>

      {!esSuperAdmin && (
        <p className="tarjeta__meta" style={{ marginTop: 14 }}>
          Renombrar, fusionar y eliminar esta reservado al super administrador.
        </p>
      )}

      {fusionando && (
        <PanelFusion categoria={fusionando} categorias={categorias}
          onCerrar={() => setFusionando(null)} />
      )}
    </>
  )
}
