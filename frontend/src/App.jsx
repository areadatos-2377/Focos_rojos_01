import { Navigate, Route, Routes } from 'react-router-dom'
import LayoutApp from './componentes/LayoutApp'
import RutaProtegida from './componentes/RutaProtegida'
import PaginaAcceso from './paginas/Login/PaginaAcceso'
import PaginaEntidades from './paginas/Entidades/PaginaEntidades'
import PaginaGaleria from './paginas/Galeria/PaginaGaleria'
import PaginaReporte from './paginas/Reporte/PaginaReporte'

function EnConstruccion({ titulo }) {
  return (
    <>
      <h1 className="titulo-pagina">{titulo}</h1>
      <div className="vacio">Esta seccion todavia no esta disponible.</div>
    </>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/acceso" element={<PaginaAcceso />} />

      <Route element={<RutaProtegida><LayoutApp /></RutaProtegida>}>
        <Route index element={<Navigate to="/entidades" replace />} />
        <Route path="entidades" element={<PaginaEntidades />} />
        <Route path="entidades/:clave" element={<PaginaGaleria />} />
        <Route path="entidades/:clave/reporte" element={<PaginaReporte />} />
        <Route
          path="reportes"
          element={<EnConstruccion titulo="Reportes generados" />}
        />
        <Route
          path="accesos"
          element={
            <RutaProtegida soloAdmin>
              <EnConstruccion titulo="Historial de accesos" />
            </RutaProtegida>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/entidades" replace />} />
    </Routes>
  )
}
