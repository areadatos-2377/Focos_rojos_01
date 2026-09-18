import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../contextos/AuthContext'
import { ROLES } from '../utilidades/formato'

const claseEnlace = ({ isActive }) =>
  `barra__enlace${isActive ? ' barra__enlace--activo' : ''}`

export default function LayoutApp() {
  const { usuario, salir, esAdmin } = useAuth()

  return (
    <div className="escenario">
      <div className="marco">
        <div className="marco__barra">
          <i /><i /><i />
          <span className="marco__titulo">Reporte Focos Rojos</span>
        </div>
        <div className="app">
          <nav className="barra">
            <div className="barra__marca">
              <span>IMSS-Bienestar</span>
              Reporte<br />Focos Rojos
            </div>

            <div className="barra__nav">
              <NavLink to="/entidades" className={claseEnlace}>
                {esAdmin ? 'Entidades' : 'Mis entidades'}
              </NavLink>
              {esAdmin && (
                <>
                  <NavLink to="/concentrado" className={claseEnlace}>Concentrado</NavLink>
                  <div className="barra__seccion">Administracion</div>
                  <NavLink to="/usuarios" className={claseEnlace}>Usuarios</NavLink>
                  <NavLink to="/categorias" className={claseEnlace}>Categorias</NavLink>
                  <NavLink to="/accesos" className={claseEnlace}>Accesos</NavLink>
                </>
              )}
            </div>

            <div className="barra__pie">
              <div className="barra__usuario">{usuario?.nombre_completo || usuario?.username}</div>
              <div className="barra__rol">
                {ROLES[usuario?.rol] ?? usuario?.rol}
                {usuario?.region ? ` · ${usuario.region.nombre}` : ''}
              </div>
              <button
                type="button"
                className="boton boton--texto"
                style={{ color: 'rgba(255,255,255,.7)', paddingLeft: 0, marginTop: 6 }}
                onClick={salir}
              >
                Cerrar sesion
              </button>
            </div>
          </nav>

          <main className="contenido">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}
