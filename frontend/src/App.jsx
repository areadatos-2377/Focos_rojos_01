import { Navigate, Route, Routes } from 'react-router-dom'
import LayoutApp from './componentes/LayoutApp'
import RutaProtegida from './componentes/RutaProtegida'
import PaginaAcceso from './paginas/Login/PaginaAcceso'
import PaginaEntidades from './paginas/Entidades/PaginaEntidades'
import PaginaGaleria from './paginas/Galeria/PaginaGaleria'
import PaginaReporte from './paginas/Reporte/PaginaReporte'
import PaginaConcentrado from './paginas/Concentrado/PaginaConcentrado'
import PaginaUsuarios from './paginas/Admin/PaginaUsuarios'
import PaginaCategorias from './paginas/Admin/PaginaCategorias'
import PaginaAccesos from './paginas/Admin/PaginaAccesos'

export default function App() {
  return (
    <Routes>
      <Route path="/acceso" element={<PaginaAcceso />} />

      <Route element={<RutaProtegida><LayoutApp /></RutaProtegida>}>
        <Route index element={<Navigate to="/entidades" replace />} />
        <Route path="entidades" element={<PaginaEntidades />} />
        <Route path="entidades/:clave" element={<PaginaGaleria />} />
        <Route path="entidades/:clave/reporte" element={<PaginaReporte />} />

        {/* Vistas de alcance nacional: solo administradores. */}
        <Route path="concentrado" element={
          <RutaProtegida soloAdmin><PaginaConcentrado /></RutaProtegida>
        } />
        <Route path="usuarios" element={
          <RutaProtegida soloAdmin><PaginaUsuarios /></RutaProtegida>
        } />
        <Route path="categorias" element={
          <RutaProtegida soloAdmin><PaginaCategorias /></RutaProtegida>
        } />
        <Route path="accesos" element={
          <RutaProtegida soloAdmin><PaginaAccesos /></RutaProtegida>
        } />
      </Route>

      <Route path="*" element={<Navigate to="/entidades" replace />} />
    </Routes>
  )
}
