import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import cliente, { mensajeDeError } from '../../api/cliente'
import { useCategorias, useEntidades, useRegiones } from '../../api/consultas'
import { DistintivoEstatus } from '../../componentes/Distintivo'
import PanelSituacion from '../Galeria/PanelSituacion'
import { ESTATUS, fechaCorta } from '../../utilidades/formato'

const SIN_AGRUPAR = ''

const AGRUPACIONES = {
  [SIN_AGRUPAR]: { etiqueta: 'Sin agrupar', clave: null },
  region: { etiqueta: 'Region', clave: (s) => s.region_nombre },
  entidad: { etiqueta: 'Entidad', clave: (s) => s.entidad_nombre },
  categoria: { etiqueta: 'Categoria', clave: (s) => s.categoria_nombre },
  estatus: { etiqueta: 'Estatus', clave: (s) => ESTATUS[s.estatus]?.etiqueta ?? s.estatus },
  orden: {
    etiqueta: 'Prioridad',
    clave: (s) => (s.orden ? `Prioridad ${s.orden}` : 'Archivadas'),
  },
}

const FILTROS_VACIOS = {
  region: '', entidad: '', categoria: '', estatus: '', orden: '', q: '',
}

/**
 * Concentrado nacional de situaciones. Solo para administradores: permite cruzar
 * datos entre estados, por ejemplo ver todas las prioridades 1 del pais o todo lo
 * que hay abierto en una categoria.
 */
export default function PaginaConcentrado() {
  const [filtros, setFiltros] = useState(FILTROS_VACIOS)
  const [agrupacion, setAgrupacion] = useState('region')
  const [archivadas, setArchivadas] = useState(false)
  const [abierta, setAbierta] = useState(null)

  const { data: regiones = [] } = useRegiones()
  const { data: entidades = [] } = useEntidades()
  const { data: categorias = [] } = useCategorias()

  const { data: situaciones = [], isLoading, error } = useQuery({
    queryKey: ['concentrado', filtros, archivadas],
    queryFn: async () => {
      const { data } = await cliente.get('/situaciones/', {
        params: {
          region: filtros.region || undefined,
          entidad_clave: filtros.entidad || undefined,
          categoria: filtros.categoria || undefined,
          estatus: filtros.estatus || undefined,
          orden: filtros.orden || undefined,
          q: filtros.q || undefined,
          archivadas: archivadas ? 'true' : undefined,
          tamano: 200,
        },
      })
      return data.results ?? data
    },
  })

  // Si se filtra por region, el desplegable de entidades solo muestra las de esa region.
  const entidadesVisibles = useMemo(
    () => (filtros.region
      ? entidades.filter((e) => e.region?.clave === filtros.region)
      : entidades),
    [entidades, filtros.region],
  )

  const grupos = useMemo(() => {
    const config = AGRUPACIONES[agrupacion]
    if (!config?.clave) return [[null, situaciones]]

    const mapa = new Map()
    for (const situacion of situaciones) {
      const clave = config.clave(situacion) ?? 'Sin dato'
      if (!mapa.has(clave)) mapa.set(clave, [])
      mapa.get(clave).push(situacion)
    }
    return [...mapa.entries()].sort(([a], [b]) => String(a).localeCompare(String(b), 'es'))
  }, [situaciones, agrupacion])

  const resumen = useMemo(() => {
    const porEstatus = { ABIERTA: 0, EN_PROCESO: 0, CERRADA: 0 }
    const entidadesConDatos = new Set()
    for (const s of situaciones) {
      porEstatus[s.estatus] = (porEstatus[s.estatus] ?? 0) + 1
      entidadesConDatos.add(s.entidad_nombre)
    }
    return { total: situaciones.length, porEstatus, entidades: entidadesConDatos.size }
  }, [situaciones])

  const cambiar = (campo) => (evento) => {
    const valor = evento.target.value
    setFiltros((previos) => ({
      ...previos,
      [campo]: valor,
      // Cambiar de region invalida la entidad elegida.
      ...(campo === 'region' ? { entidad: '' } : {}),
    }))
  }

  const hayFiltros = Object.values(filtros).some(Boolean)

  if (error) return <div className="aviso aviso--error">{mensajeDeError(error)}</div>

  return (
    <>
      <p className="antetitulo">Administracion</p>
      <h1 className="titulo-pagina">Concentrado de situaciones</h1>
      <p className="subtitulo">
        Todas las situaciones del pais. Filtra y agrupa para comparar entre estados.
      </p>

      <div className="resumen">
        <div className="resumen__dato">
          <div className="resumen__cifra">{resumen.total}</div>
          <div className="resumen__etiqueta">Situaciones</div>
        </div>
        <div className="resumen__dato">
          <div className="resumen__cifra">{resumen.entidades}</div>
          <div className="resumen__etiqueta">Entidades</div>
        </div>
        <div className="resumen__dato resumen__dato--acento">
          <div className="resumen__cifra">{resumen.porEstatus.ABIERTA}</div>
          <div className="resumen__etiqueta">Abiertas</div>
        </div>
        <div className="resumen__dato">
          <div className="resumen__cifra">{resumen.porEstatus.EN_PROCESO}</div>
          <div className="resumen__etiqueta">En proceso</div>
        </div>
      </div>

      <div className="filtros">
        <div className="filtros__campo">
          <label className="filtros__etiqueta" htmlFor="f-region">Region</label>
          <select id="f-region" className="filtros__control"
            value={filtros.region} onChange={cambiar('region')}>
            <option value="">Todas</option>
            {regiones.map((r) => <option key={r.id} value={r.clave}>{r.nombre}</option>)}
          </select>
        </div>

        <div className="filtros__campo">
          <label className="filtros__etiqueta" htmlFor="f-entidad">Entidad</label>
          <select id="f-entidad" className="filtros__control"
            value={filtros.entidad} onChange={cambiar('entidad')}>
            <option value="">Todas</option>
            {entidadesVisibles.map((e) => (
              <option key={e.id} value={e.clave}>{e.nombre}</option>
            ))}
          </select>
        </div>

        <div className="filtros__campo">
          <label className="filtros__etiqueta" htmlFor="f-categoria">Categoria</label>
          <select id="f-categoria" className="filtros__control"
            value={filtros.categoria} onChange={cambiar('categoria')}>
            <option value="">Todas</option>
            {categorias.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </div>

        <div className="filtros__campo">
          <label className="filtros__etiqueta" htmlFor="f-estatus">Estatus</label>
          <select id="f-estatus" className="filtros__control"
            value={filtros.estatus} onChange={cambiar('estatus')}>
            <option value="">Todos</option>
            <option value="ABIERTA">Abierta</option>
            <option value="EN_PROCESO">En proceso</option>
            <option value="CERRADA">Cerrada</option>
          </select>
        </div>

        <div className="filtros__campo">
          <label className="filtros__etiqueta" htmlFor="f-orden">Prioridad</label>
          <select id="f-orden" className="filtros__control"
            value={filtros.orden} onChange={cambiar('orden')}>
            <option value="">Todas</option>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n === 1 ? '1 (las mas urgentes)' : n}
              </option>
            ))}
          </select>
        </div>

        <div className="filtros__campo" style={{ flex: 1, minWidth: 190 }}>
          <label className="filtros__etiqueta" htmlFor="f-q">Buscar</label>
          <input id="f-q" className="filtros__control" style={{ width: '100%' }}
            placeholder="Tema o responsable…"
            value={filtros.q} onChange={cambiar('q')} />
        </div>

        <div className="filtros__campo">
          <label className="filtros__etiqueta" htmlFor="f-agrupar">Agrupar por</label>
          <select id="f-agrupar" className="filtros__control"
            value={agrupacion} onChange={(e) => setAgrupacion(e.target.value)}>
            {Object.entries(AGRUPACIONES).map(([clave, { etiqueta }]) => (
              <option key={clave} value={clave}>{etiqueta}</option>
            ))}
          </select>
        </div>

        <button type="button"
          className={`chip${archivadas ? ' chip--activo' : ''}`}
          style={{ marginBottom: 2 }}
          onClick={() => setArchivadas((v) => !v)}>
          {archivadas ? 'Viendo archivadas' : 'Ver archivadas'}
        </button>

        {hayFiltros && (
          <button type="button" className="boton boton--texto"
            onClick={() => setFiltros(FILTROS_VACIOS)}>
            Limpiar filtros
          </button>
        )}
      </div>

      {isLoading && <p className="cargando">Cargando concentrado…</p>}

      {!isLoading && situaciones.length === 0 && (
        <div className="vacio">
          Ninguna situacion coincide con los filtros seleccionados.
        </div>
      )}

      {!isLoading && situaciones.length > 0 && (
        <div className="tabla-caja">
          <table className="tabla">
            <thead>
              <tr>
                <th style={{ width: 52 }}>Prio.</th>
                <th>Entidad</th>
                <th>Region</th>
                <th>Categoria</th>
                <th>Tema</th>
                <th>Estatus</th>
                <th>Responsable</th>
                <th>Inicio</th>
              </tr>
            </thead>
            <tbody>
              {grupos.map(([nombreGrupo, delGrupo]) => (
                <Grupo key={nombreGrupo ?? 'todo'} nombre={nombreGrupo}
                  situaciones={delGrupo} onAbrir={setAbierta} />
              ))}
            </tbody>
          </table>
          <div className="tabla__pie">
            {situaciones.length} situaciones
            {agrupacion && ` · agrupadas por ${AGRUPACIONES[agrupacion].etiqueta.toLowerCase()}`}
          </div>
        </div>
      )}

      {abierta && (
        <PanelSituacion
          situacionId={abierta.id}
          entidadClave={abierta.entidad}
          onCerrar={() => setAbierta(null)}
          onEditar={() => setAbierta(null)}
        />
      )}
    </>
  )
}

function Grupo({ nombre, situaciones, onAbrir }) {
  return (
    <>
      {nombre && (
        <tr className="tabla__grupo">
          <td colSpan={8}>
            {nombre} <span>· {situaciones.length}</span>
          </td>
        </tr>
      )}
      {situaciones.map((s) => (
        <tr key={s.id}>
          <td>
            <span className={`tabla__prioridad${
              s.orden === 1 ? ' tabla__prioridad--top'
                : s.orden ? '' : ' tabla__prioridad--sin'}`}>
              {s.orden ?? '–'}
            </span>
          </td>
          <td className="tabla__entidad">{s.entidad_nombre}</td>
          <td style={{ color: 'var(--gray-tx)', whiteSpace: 'nowrap' }}>{s.region_nombre}</td>
          <td style={{ whiteSpace: 'nowrap' }}>{s.categoria_nombre}</td>
          <td>
            <button type="button" className="tabla__tema" onClick={() => onAbrir(s)}>
              {s.tema.length > 210 ? `${s.tema.slice(0, 210)}…` : s.tema}
            </button>
          </td>
          <td><DistintivoEstatus estatus={s.estatus} /></td>
          <td style={{ color: 'var(--gray-tx)' }}>{s.responsable}</td>
          <td style={{ whiteSpace: 'nowrap', color: 'var(--gray-tx)' }}>
            {fechaCorta(s.fecha_inicio) || '—'}
          </td>
        </tr>
      ))}
    </>
  )
}
