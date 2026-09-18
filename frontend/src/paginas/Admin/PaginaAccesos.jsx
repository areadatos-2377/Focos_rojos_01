import { useState } from 'react'
import { mensajeDeError } from '../../api/cliente'
import { useAccesos, useUsuarios } from '../../api/consultas'
import { ROLES, fechaHora } from '../../utilidades/formato'

export default function PaginaAccesos() {
  const [usuarioId, setUsuarioId] = useState('')
  const { data: usuarios = [] } = useUsuarios()
  const { data: accesos = [], isLoading, error } = useAccesos(usuarioId)

  if (error) return <div className="aviso aviso--error">{mensajeDeError(error)}</div>

  return (
    <>
      <p className="antetitulo">Administracion</p>
      <h1 className="titulo-pagina">Historial de accesos</h1>
      <p className="subtitulo">
        Cada inicio de sesion exitoso. Solo lo ven administradores y super administradores.
      </p>

      <div className="filtros">
        <div className="filtros__campo">
          <label className="filtros__etiqueta" htmlFor="usuario">Usuario</label>
          <select id="usuario" className="filtros__control" value={usuarioId}
            onChange={(e) => setUsuarioId(e.target.value)}>
            <option value="">Todos</option>
            {usuarios.map((u) => (
              <option key={u.id} value={u.id}>
                {u.nombre_completo || u.username}
              </option>
            ))}
          </select>
        </div>
      </div>

      {isLoading && <p className="cargando">Cargando accesos…</p>}

      {!isLoading && accesos.length === 0 && (
        <div className="vacio">Todavia no hay accesos registrados.</div>
      )}

      {accesos.length > 0 && (
        <div className="tabla-caja">
          <table className="tabla">
            <thead>
              <tr>
                <th>Fecha y hora</th>
                <th>Usuario</th>
                <th>Rol</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {accesos.map((a) => (
                <tr key={a.id}>
                  <td style={{ whiteSpace: 'nowrap' }}>{fechaHora(a.creado_en)}</td>
                  <td className="tabla__entidad">{a.usuario_nombre || a.username}</td>
                  <td style={{ color: 'var(--gray-tx)' }}>{ROLES[a.rol] ?? a.rol}</td>
                  <td className="mono" style={{ color: 'var(--gray-tx)' }}>{a.ip || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="tabla__pie">{accesos.length} accesos registrados</div>
        </div>
      )}
    </>
  )
}
