import { Navigate } from 'react-router-dom'
import { useAuth } from '../contextos/AuthContext'

export default function RutaProtegida({ children, soloAdmin = false }) {
  const { autenticado, cargando, esAdmin } = useAuth()

  if (cargando) return <p className="cargando" style={{ padding: 40 }}>Cargando sesion…</p>
  if (!autenticado) return <Navigate to="/acceso" replace />
  if (soloAdmin && !esAdmin) return <Navigate to="/" replace />

  return children
}
