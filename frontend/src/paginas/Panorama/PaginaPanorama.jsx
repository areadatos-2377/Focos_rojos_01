import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import cliente, { mensajeDeError } from '../../api/cliente'
import {
  COLUMNAS, CUADRICULA, FILAS, RAMPA, SIN_DATOS, TINTA, TINTA_SIN_DATOS,
  escalon, rangosLeyenda,
} from './mapa'

const METRICAS = {
  abiertas: { etiqueta: 'Situaciones abiertas', corto: 'abiertas' },
  en_proceso: { etiqueta: 'En proceso', corto: 'en proceso' },
  activas: { etiqueta: 'Total activas', corto: 'activas' },
}

function Indicador({ cifra, etiqueta, acento = false }) {
  return (
    <div className={`resumen__dato${acento ? ' resumen__dato--acento' : ''}`}>
      <div className="resumen__cifra">{cifra}</div>
      <div className="resumen__etiqueta">{etiqueta}</div>
    </div>
  )
}

function Leyenda({ maximo, titulo }) {
  const rangos = rangosLeyenda(maximo)
  return (
    <div className="leyenda">
      <span className="leyenda__titulo">{titulo}</span>
      <span className="leyenda__paso">
        <i style={{ background: SIN_DATOS, borderColor: '#E7E2D9' }} />
        ninguna
      </span>
      {rangos.map((r) => (
        <span key={r.etiqueta} className="leyenda__paso">
          <i style={{ background: r.color, borderColor: r.color }} />
          {r.etiqueta}
        </span>
      ))}
    </div>
  )
}

export default function PaginaPanorama() {
  const navegar = useNavigate()
  const [metrica, setMetrica] = useState('abiertas')
  const [verTabla, setVerTabla] = useState(false)
  const [encima, setEncima] = useState(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['panorama'],
    queryFn: async () => (await cliente.get('/panorama/')).data,
  })

  const porClave = useMemo(() => {
    const mapa = new Map()
    for (const e of data?.entidades ?? []) mapa.set(e.clave, e)
    return mapa
  }, [data])

  const maximoMapa = useMemo(
    () => Math.max(1, ...(data?.entidades ?? []).map((e) => e[metrica] ?? 0)),
    [data, metrica],
  )

  const { regiones, categorias, celdas, maximoMatriz } = useMemo(() => {
    const filas = data?.matriz ?? []
    const regs = [...new Set(filas.map((f) => f.region))].sort((a, b) =>
      a.localeCompare(b, 'es'))
    const cats = [...new Set(filas.map((f) => f.categoria))].sort((a, b) =>
      a.localeCompare(b, 'es'))
    const mapa = new Map(filas.map((f) => [`${f.region}|${f.categoria}`, f.total]))
    return {
      regiones: regs,
      categorias: cats,
      celdas: mapa,
      maximoMatriz: Math.max(1, ...filas.map((f) => f.total)),
    }
  }, [data])

  if (isLoading) return <p className="cargando">Cargando panorama…</p>
  if (error) return <div className="aviso aviso--error">{mensajeDeError(error)}</div>

  const t = data.totales

  return (
    <>
      <p className="antetitulo">Vision nacional</p>
      <h1 className="titulo-pagina">Panorama</h1>
      <p className="subtitulo">
        Donde se concentran los focos rojos del pais. Cada pieza es una entidad;
        el color indica cuantas situaciones tiene.
      </p>

      <div className="resumen">
        <Indicador cifra={t.activas} etiqueta="Situaciones activas" />
        <Indicador cifra={t.abiertas} etiqueta="Abiertas" acento />
        <Indicador cifra={t.en_proceso} etiqueta="En proceso" />
        <Indicador cifra={t.entidades} etiqueta="Entidades" />
        <Indicador cifra={t.archivadas} etiqueta="Archivadas" />
      </div>

      {/* Controles en una sola fila, antes de los graficos. */}
      <div className="filtros" style={{ alignItems: 'center' }}>
        <div className="filtros__campo">
          <label className="filtros__etiqueta" htmlFor="metrica">Colorear por</label>
          <select id="metrica" className="filtros__control" value={metrica}
            onChange={(e) => setMetrica(e.target.value)}>
            {Object.entries(METRICAS).map(([clave, { etiqueta }]) => (
              <option key={clave} value={clave}>{etiqueta}</option>
            ))}
          </select>
        </div>
        <span className="barra-acciones__espacio" />
        <button type="button" className={`chip${verTabla ? ' chip--activo' : ''}`}
          onClick={() => setVerTabla((v) => !v)}>
          {verTabla ? 'Ver graficos' : 'Ver como tabla'}
        </button>
      </div>

      {verTabla ? (
        <TablaPanorama entidades={data.entidades} />
      ) : (
        <>
          <section className="panel-grafico">
            <header className="panel-grafico__cabeza">
              <h2>{METRICAS[metrica].etiqueta} por entidad</h2>
              <Leyenda maximo={maximoMapa} titulo="Situaciones" />
            </header>

            <div className="mosaico"
              style={{ gridTemplateColumns: `repeat(${COLUMNAS}, 1fr)`,
                       gridTemplateRows: `repeat(${FILAS}, 1fr)` }}>
              {Object.entries(CUADRICULA).map(([clave, pos]) => {
                const entidad = porClave.get(clave)
                if (!entidad) return null
                const valor = entidad[metrica] ?? 0
                const paso = escalon(valor, maximoMapa)
                const fondo = paso < 0 ? SIN_DATOS : RAMPA[paso]
                const tinta = paso < 0 ? TINTA_SIN_DATOS : TINTA[paso]

                return (
                  <button
                    key={clave}
                    type="button"
                    className="mosaico__pieza"
                    style={{
                      gridRow: pos.fila + 1,
                      gridColumn: pos.columna + 1,
                      background: fondo,
                      color: tinta,
                    }}
                    onMouseEnter={() => setEncima(entidad)}
                    onMouseLeave={() => setEncima(null)}
                    onFocus={() => setEncima(entidad)}
                    onBlur={() => setEncima(null)}
                    onClick={() => navegar(`/entidades/${clave}`)}
                    aria-label={`${entidad.nombre}: ${valor} ${METRICAS[metrica].corto}`}
                  >
                    <span className="mosaico__sigla">{pos.sigla}</span>
                    <span className="mosaico__cifra">{valor}</span>
                  </button>
                )
              })}
            </div>

            <div className="mosaico__pie">
              {encima ? (
                <>
                  <strong>{encima.nombre}</strong> · {encima.region} ·{' '}
                  {encima.abiertas} abiertas, {encima.en_proceso} en proceso
                  {encima.archivadas > 0 && `, ${encima.archivadas} archivadas`}
                </>
              ) : (
                'Pasa el cursor sobre una entidad para ver su detalle. Haz clic para abrirla.'
              )}
            </div>
          </section>

          <section className="panel-grafico">
            <header className="panel-grafico__cabeza">
              <h2>Concentracion por region y categoria</h2>
              <Leyenda maximo={maximoMatriz} titulo="Situaciones" />
            </header>

            <div className="matriz-caja">
              <table className="matriz">
                <thead>
                  <tr>
                    <th />
                    {categorias.map((c) => (
                      <th key={c}><span>{c}</span></th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {regiones.map((region) => (
                    <tr key={region}>
                      <th scope="row">{region}</th>
                      {categorias.map((categoria) => {
                        const valor = celdas.get(`${region}|${categoria}`) ?? 0
                        const paso = escalon(valor, maximoMatriz)
                        return (
                          <td key={categoria}>
                            <span
                              className="matriz__celda"
                              style={{
                                background: paso < 0 ? SIN_DATOS : RAMPA[paso],
                                color: paso < 0 ? TINTA_SIN_DATOS : TINTA[paso],
                              }}
                              title={`${region} · ${categoria}: ${valor}`}
                            >
                              {valor || '·'}
                            </span>
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  )
}

function TablaPanorama({ entidades }) {
  return (
    <div className="tabla-caja">
      <table className="tabla">
        <thead>
          <tr>
            <th>Entidad</th>
            <th>Region</th>
            <th>Abiertas</th>
            <th>En proceso</th>
            <th>Activas</th>
            <th>Archivadas</th>
          </tr>
        </thead>
        <tbody>
          {entidades.map((e) => (
            <tr key={e.clave}>
              <td className="tabla__entidad">{e.nombre}</td>
              <td style={{ color: 'var(--gray-tx)' }}>{e.region}</td>
              <td>{e.abiertas}</td>
              <td>{e.en_proceso}</td>
              <td>{e.activas}</td>
              <td style={{ color: 'var(--gray-tx)' }}>{e.archivadas}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="tabla__pie">{entidades.length} entidades</div>
    </div>
  )
}
