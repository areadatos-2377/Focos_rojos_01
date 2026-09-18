import { Link } from 'react-router-dom'
import { useEntidades } from '../../api/consultas'
import { useAuth } from '../../contextos/AuthContext'
import { agruparPorRegion } from '../../utilidades/formato'
import { mensajeDeError } from '../../api/cliente'

function Tarjeta({ entidad }) {
  return (
    <Link to={`/entidades/${entidad.clave}`} className="tarjeta">
      <div className="tarjeta__nombre">{entidad.nombre}</div>
      <div className="tarjeta__meta">{entidad.region?.nombre}</div>
    </Link>
  )
}

export default function PaginaEntidades() {
  const { esAdmin, usuario } = useAuth()
  const { data: entidades, isLoading, error } = useEntidades()

  if (isLoading) return <p className="cargando">Cargando entidades…</p>
  if (error) return <div className="aviso aviso--error">{mensajeDeError(error)}</div>

  const grupos = agruparPorRegion(entidades)

  return (
    <>
      <p className="antetitulo">Focos rojos</p>
      <h1 className="titulo-pagina">{esAdmin ? 'Entidades' : 'Mis entidades'}</h1>
      <p className="subtitulo">
        {esAdmin
          ? `${entidades.length} entidades agrupadas por region operativa.`
          : `Region ${usuario?.region?.nombre}: ${entidades.length} entidades a tu cargo.`}
      </p>

      {/* Los administradores ven el agrupador de region; un regional solo tiene
          una region, asi que para el seria ruido. */}
      {esAdmin ? (
        grupos.map(([region, deLaRegion]) => (
          <section key={region}>
            <h2 className="seccion-region">
              {region}
              <small>{deLaRegion.length} entidades</small>
            </h2>
            <div className="rejilla">
              {deLaRegion.map((e) => <Tarjeta key={e.id} entidad={e} />)}
            </div>
          </section>
        ))
      ) : (
        <div className="rejilla">
          {entidades.map((e) => <Tarjeta key={e.id} entidad={e} />)}
        </div>
      )}
    </>
  )
}
