import { useState } from 'react'
import { useCategorias, useCrearCategoria } from '../api/consultas'
import { mensajeDeError } from '../api/cliente'

/**
 * Lista desplegable de categorias con opcion de agregar una nueva.
 * La API es idempotente: si la categoria ya existe (aunque este escrita con otras
 * mayusculas o acentos) devuelve la existente en vez de duplicarla.
 */
export default function SelectorCategoria({ valor, onCambio, error }) {
  const { data: categorias = [], isLoading } = useCategorias()
  const crear = useCrearCategoria()
  const [agregando, setAgregando] = useState(false)
  const [nombre, setNombre] = useState('')
  const [fallo, setFallo] = useState(null)

  const confirmar = async () => {
    setFallo(null)
    try {
      const categoria = await crear.mutateAsync(nombre.trim())
      onCambio(categoria.id)
      setAgregando(false)
      setNombre('')
    } catch (e) {
      setFallo(mensajeDeError(e, 'No se pudo crear la categoria.'))
    }
  }

  if (agregando) {
    return (
      <div className="campo">
        <label className="campo__etiqueta" htmlFor="nueva-categoria">Nueva categoria</label>
        <input
          id="nueva-categoria"
          className="campo__control"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder="Por ejemplo: Equipamiento medico"
          autoFocus
        />
        {fallo && <p className="campo__error">{fallo}</p>}
        <div className="barra-acciones" style={{ marginTop: 9 }}>
          <button
            type="button"
            className="boton boton--primario"
            onClick={confirmar}
            disabled={nombre.trim().length < 3 || crear.isPending}
          >
            Agregar
          </button>
          <button
            type="button"
            className="boton boton--texto"
            onClick={() => { setAgregando(false); setFallo(null) }}
          >
            Cancelar
          </button>
        </div>
        <p className="tarjeta__meta">
          Quedara disponible para todos los usuarios, asi no se repite la misma
          categoria con nombres distintos.
        </p>
      </div>
    )
  }

  return (
    <div className="campo">
      <label className="campo__etiqueta" htmlFor="categoria">Categoria</label>
      <select
        id="categoria"
        className="campo__control"
        value={valor ?? ''}
        onChange={(e) => onCambio(e.target.value ? Number(e.target.value) : null)}
        disabled={isLoading}
      >
        <option value="">Selecciona una categoria…</option>
        {categorias.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
      </select>
      {error && <p className="campo__error">{error}</p>}
      <button
        type="button"
        className="boton boton--texto"
        style={{ paddingLeft: 0 }}
        onClick={() => setAgregando(true)}
      >
        + Agregar una categoria nueva
      </button>
    </div>
  )
}
