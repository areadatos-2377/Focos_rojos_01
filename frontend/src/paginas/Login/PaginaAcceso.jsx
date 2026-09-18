import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contextos/AuthContext'
import { mensajeDeError } from '../../api/cliente'

export default function PaginaAcceso() {
  const { entrar, autenticado, cargando } = useAuth()
  const navegar = useNavigate()
  const [datos, setDatos] = useState({ username: '', password: '' })
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  if (cargando) return <p className="cargando" style={{ padding: 40 }}>Cargando…</p>
  if (autenticado) return <Navigate to="/entidades" replace />

  const enviar = async (evento) => {
    evento.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await entrar(datos.username.trim(), datos.password)
      navegar('/entidades', { replace: true })
    } catch (fallo) {
      setError(
        fallo?.response?.status === 401
          ? 'Usuario o contrasena incorrectos.'
          : mensajeDeError(fallo, 'No se pudo iniciar sesion.'),
      )
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="acceso">
      <form className="acceso__caja" onSubmit={enviar}>
        <p className="antetitulo">IMSS-Bienestar</p>
        <h1 style={{ fontSize: 27, margin: '0 0 22px', color: 'var(--verde-d)' }}>
          Reporte Focos Rojos
        </h1>

        {error && <div className="aviso aviso--error">{error}</div>}

        <div className="campo">
          <label className="campo__etiqueta" htmlFor="username">Usuario</label>
          <input
            id="username"
            className="campo__control"
            autoComplete="username"
            autoFocus
            value={datos.username}
            onChange={(e) => setDatos({ ...datos, username: e.target.value })}
            required
          />
        </div>

        <div className="campo">
          <label className="campo__etiqueta" htmlFor="password">Contrasena</label>
          <input
            id="password"
            type="password"
            className="campo__control"
            autoComplete="current-password"
            value={datos.password}
            onChange={(e) => setDatos({ ...datos, password: e.target.value })}
            required
          />
        </div>

        <button
          type="submit"
          className="boton boton--primario"
          style={{ width: '100%', marginTop: 8 }}
          disabled={enviando}
        >
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}
