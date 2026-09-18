import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../contextos/AuthContext'
import { ROLES } from '../utilidades/formato'
import {
  DefinicionDegradado,
  IconoAccesos,
  IconoCategorias,
  IconoConcentrado,
  IconoEntidades,
  IconoPanorama,
  IconoUsuarios,
} from './Iconos'

const claseEnlace = ({ isActive }) =>
  `barra__enlace${isActive ? ' barra__enlace--activo' : ''}`

function Enlace({ a, Icono, children }) {
  return (
    <NavLink to={a} className={claseEnlace}>
      <Icono />
      <span>{children}</span>
    </NavLink>
  )
}

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
            <DefinicionDegradado />

            <div className="barra__marca">
              <span>IMSS-Bienestar</span>
              Reporte<br />Focos Rojos
            </div>

            <div className="barra__nav">
              <Enlace a="/entidades" Icono={IconoEntidades}>
                {esAdmin ? 'Entidades' : 'Mis entidades'}
              </Enlace>

              {esAdmin && (
                <>
                  <Enlace a="/panorama" Icono={IconoPanorama}>Panorama</Enlace>
                  <Enlace a="/concentrado" Icono={IconoConcentrado}>Concentrado</Enlace>

                  <div className="barra__seccion">Administracion</div>

                  <Enlace a="/usuarios" Icono={IconoUsuarios}>Usuarios</Enlace>
                  <Enlace a="/categorias" Icono={IconoCategorias}>Categorias</Enlace>
                  <Enlace a="/accesos" Icono={IconoAccesos}>Accesos</Enlace>
                </>
              )}
            </div>

            <div className="barra__pie">
              <div className="barra__usuario">
                {usuario?.nombre_completo || usuario?.username}
              </div>
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
