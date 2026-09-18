import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import cliente, { mensajeDeError } from '../../api/cliente'
import { useEntidades, useSituaciones } from '../../api/consultas'
import { DistintivoCategoria, DistintivoEstatus } from '../../componentes/Distintivo'
import { fechaCorta } from '../../utilidades/formato'

const MAXIMO = 5

const hoy = () => new Date().toISOString().slice(0, 10)

export default function PaginaReporte() {
  const { clave } = useParams()
  const { data: entidades = [] } = useEntidades()
  const entidad = entidades.find((e) => e.clave === clave)
  const { data: situaciones = [], isLoading } = useSituaciones(clave, false)

  const [portada, setPortada] = useState({
    fecha_corte: hoy(),
    fecha_entrega: hoy(),
    responsable_reporte: '',
  })
  const [elegidas, setElegidas] = useState([])
  const [urlPrevia, setUrlPrevia] = useState(null)
  const [generando, setGenerando] = useState(false)
  const [error, setError] = useState(null)

  // Sugerencia inicial: las 5 mas urgentes segun el orden de la galeria.
  useEffect(() => {
    if (situaciones.length && elegidas.length === 0) {
      setElegidas(situaciones.slice(0, MAXIMO).map((s) => s.id))
    }
  }, [situaciones]) // eslint-disable-line react-hooks/exhaustive-deps

  // El PDF vive como blob en memoria: hay que liberarlo al cambiarlo o salir.
  useEffect(() => () => { if (urlPrevia) URL.revokeObjectURL(urlPrevia) }, [urlPrevia])

  const alternar = (id) => {
    // La decision se toma fuera del actualizador de estado: React puede invocarlo
    // dos veces en modo estricto, y un setError ahi dentro se disparia repetido.
    if (elegidas.includes(id)) {
      setError(null)
      setElegidas(elegidas.filter((x) => x !== id))
      return
    }
    if (elegidas.length >= MAXIMO) {
      setError(`El formato admite un maximo de ${MAXIMO} situaciones.`)
      return
    }
    setError(null)
    setElegidas([...elegidas, id])
  }

  const pedirDocumento = async (formato) => {
    const { data } = await cliente.post(
      '/reportes/vista-previa/',
      { entidad: clave, ...portada, situaciones: elegidas, formato },
      { responseType: 'blob' },
    )
    return data
  }

  const generar = async () => {
    setError(null)
    setGenerando(true)
    try {
      const blob = await pedirDocumento('pdf')
      if (urlPrevia) URL.revokeObjectURL(urlPrevia)
      setUrlPrevia(URL.createObjectURL(blob))
    } catch (fallo) {
      // Con responseType blob, el cuerpo del error tambien llega como blob.
      let detalle = 'No se pudo generar el reporte.'
      try {
        detalle = mensajeDeError(
          { response: { data: JSON.parse(await fallo.response.data.text()) } },
          detalle,
        )
      } catch { /* se queda el mensaje generico */ }
      setError(detalle)
    } finally {
      setGenerando(false)
    }
  }

  const descargar = async (formato) => {
    try {
      const blob = await pedirDocumento(formato)
      const url = URL.createObjectURL(blob)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = `focos-rojos_${clave}_${portada.fecha_corte}.${formato}`
      enlace.click()
      URL.revokeObjectURL(url)
    } catch (fallo) {
      setError(mensajeDeError(fallo, 'No se pudo descargar el archivo.'))
    }
  }

  const listo = elegidas.length > 0 && portada.responsable_reporte.trim().length >= 3

  return (
    <>
      <p className="antetitulo">
        <Link to={`/entidades/${clave}`} style={{ textDecoration: 'none' }}>
          ← Volver a {entidad?.nombre ?? clave}
        </Link>
      </p>
      <h1 className="titulo-pagina">Generar Reporte Focos Rojos</h1>
      <p className="subtitulo">
        Top {MAXIMO} focos rojos de {entidad?.nombre ?? clave}.
      </p>

      {error && <div className="aviso aviso--error">{error}</div>}

      <section style={{ maxWidth: 620 }}>
        <h2 className="seccion-region">1. Datos de portada</h2>

        <div className="campo">
          <label className="campo__etiqueta">Estado</label>
          <input className="campo__control" value={entidad?.nombre ?? ''} disabled />
        </div>

        <div className="campo__fila">
          <div className="campo">
            <label className="campo__etiqueta" htmlFor="corte">Fecha de corte</label>
            <input id="corte" type="date" className="campo__control"
              value={portada.fecha_corte}
              onChange={(e) => setPortada({ ...portada, fecha_corte: e.target.value })} />
          </div>
          <div className="campo">
            <label className="campo__etiqueta" htmlFor="entrega">Fecha de entrega</label>
            <input id="entrega" type="date" className="campo__control"
              value={portada.fecha_entrega}
              onChange={(e) => setPortada({ ...portada, fecha_entrega: e.target.value })} />
          </div>
        </div>

        <div className="campo">
          <label className="campo__etiqueta" htmlFor="responsable">
            Responsable que llena el reporte
          </label>
          <input id="responsable" className="campo__control"
            value={portada.responsable_reporte}
            placeholder="Nombre de quien entrega el reporte"
            onChange={(e) => setPortada({ ...portada, responsable_reporte: e.target.value })} />
        </div>
      </section>

      <section>
        <h2 className="seccion-region">
          2. Situaciones a incluir
          <small>{elegidas.length} de {MAXIMO}</small>
        </h2>

        {isLoading && <p className="cargando">Cargando situaciones…</p>}
        {!isLoading && situaciones.length === 0 && (
          <div className="vacio">No hay situaciones activas en esta entidad.</div>
        )}

        <div style={{ display: 'grid', gap: 8 }}>
          {situaciones.map((s) => {
            const posicion = elegidas.indexOf(s.id)
            const marcada = posicion >= 0
            return (
              <label key={s.id} className="ficha"
                style={{
                  cursor: 'pointer',
                  borderColor: marcada ? 'var(--verde)' : undefined,
                  gridTemplateColumns: '38px 1fr auto',
                }}>
                <span className={`ficha__orden${marcada ? '' : ' ficha__orden--top'}`}
                  style={{
                    cursor: 'pointer',
                    background: marcada ? 'var(--verde)' : 'var(--gray)',
                  }}>
                  {marcada ? posicion + 1 : '–'}
                </span>
                <span>
                  <span style={{ fontWeight: 600 }}>{s.tema}</span>
                  <span className="ficha__pie">
                    <DistintivoEstatus estatus={s.estatus} />
                    <DistintivoCategoria nombre={s.categoria_nombre} />
                    <span className="tarjeta__meta">
                      Inicio {fechaCorta(s.fecha_inicio)}
                    </span>
                  </span>
                </span>
                <input type="checkbox" checked={marcada} onChange={() => alternar(s.id)} />
              </label>
            )
          })}
        </div>
        <p className="tarjeta__meta" style={{ marginTop: 8 }}>
          El numero indica en que posicion saldra en el documento: se asigna segun el
          orden en que las vas marcando.
        </p>
      </section>

      <section>
        <h2 className="seccion-region">3. Vista previa</h2>

        <div className="barra-acciones">
          <button type="button" className="boton boton--primario"
            onClick={generar} disabled={!listo || generando}>
            {generando ? 'Generando…' : 'Generar vista previa'}
          </button>
          <button type="button" className="boton boton--neutro"
            onClick={() => descargar('docx')} disabled={!listo}>
            Descargar .docx
          </button>
          <button type="button" className="boton boton--neutro"
            onClick={() => descargar('pdf')} disabled={!listo}>
            Descargar .pdf
          </button>
        </div>

        {!listo && (
          <p className="tarjeta__meta">
            Indica el responsable y elige al menos una situacion.
          </p>
        )}

        {urlPrevia ? (
          <iframe
            title="Vista previa del reporte"
            src={urlPrevia}
            style={{
              width: '100%', height: 760, border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', background: 'var(--paper)',
            }}
          />
        ) : (
          <div className="vacio">
            La vista previa aparecera aqui. Es el mismo documento que se guardara.
          </div>
        )}
      </section>
    </>
  )
}
