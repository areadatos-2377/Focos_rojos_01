import { useState } from 'react'
import { mensajeDeError } from '../../api/cliente'
import {
  useGuardarUsuario, useRegiones, useResetearPassword, useUsuarios,
} from '../../api/consultas'
import { useAuth } from '../../contextos/AuthContext'
import Panel from '../../componentes/Panel'
import { ROLES, fechaHora } from '../../utilidades/formato'

const VACIO = {
  username: '', nombre_completo: '', email: '',
  rol: 'REGIONAL', region: '', password: '', is_active: true,
}

function FormularioUsuario({ usuario, onCerrar }) {
  const esNuevo = !usuario?.id
  const { data: regiones = [] } = useRegiones()
  const guardar = useGuardarUsuario()
  const [datos, setDatos] = useState({ ...VACIO, ...usuario, password: '' })
  const [fallo, setFallo] = useState(null)

  const cambiar = (campo) => (e) =>
    setDatos((p) => ({ ...p, [campo]: e.target.value }))

  const esRegional = datos.rol === 'REGIONAL'

  const enviar = async (evento) => {
    evento.preventDefault()
    setFallo(null)

    const cuerpo = {
      username: datos.username.trim(),
      nombre_completo: datos.nombre_completo.trim(),
      email: datos.email.trim(),
      rol: datos.rol,
      // Un usuario que no es regional no conserva region.
      region: esRegional ? Number(datos.region) || null : null,
      is_active: datos.is_active,
    }
    if (datos.password) cuerpo.password = datos.password

    try {
      await guardar.mutateAsync(esNuevo ? cuerpo : { id: usuario.id, ...cuerpo })
      onCerrar()
    } catch (error) {
      setFallo(mensajeDeError(error, 'No se pudo guardar el usuario.'))
    }
  }

  return (
    <Panel titulo={esNuevo ? 'Nueva cuenta' : `Editar ${usuario.username}`} onCerrar={onCerrar}>
      <form onSubmit={enviar}>
        {fallo && <div className="aviso aviso--error">{fallo}</div>}

        <div className="campo__fila">
          <div className="campo">
            <label className="campo__etiqueta" htmlFor="username">Usuario</label>
            <input id="username" className="campo__control" value={datos.username}
              onChange={cambiar('username')} disabled={!esNuevo} required />
            {!esNuevo && <p className="tarjeta__meta">El usuario no se puede cambiar.</p>}
          </div>
          <div className="campo">
            <label className="campo__etiqueta" htmlFor="nombre">Nombre completo</label>
            <input id="nombre" className="campo__control" value={datos.nombre_completo}
              onChange={cambiar('nombre_completo')} required />
          </div>
        </div>

        <div className="campo">
          <label className="campo__etiqueta" htmlFor="email">Correo</label>
          <input id="email" type="email" className="campo__control" value={datos.email}
            onChange={cambiar('email')} />
        </div>

        <div className="campo__fila">
          <div className="campo">
            <label className="campo__etiqueta" htmlFor="rol">Rol</label>
            <select id="rol" className="campo__control" value={datos.rol}
              onChange={cambiar('rol')}>
              <option value="REGIONAL">Regional</option>
              <option value="ADMINISTRADOR">Administrador</option>
              <option value="SUPER_ADMIN">Super administrador</option>
            </select>
          </div>
          <div className="campo">
            <label className="campo__etiqueta" htmlFor="region">Region</label>
            <select id="region" className="campo__control" value={datos.region ?? ''}
              onChange={cambiar('region')} disabled={!esRegional} required={esRegional}>
              <option value="">{esRegional ? 'Selecciona…' : 'No aplica'}</option>
              {regiones.map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}
            </select>
            <p className="tarjeta__meta">
              {esRegional
                ? 'Obligatoria: define que entidades podra ver.'
                : 'Los administradores ven todas las entidades.'}
            </p>
          </div>
        </div>

        <div className="campo">
          <label className="campo__etiqueta" htmlFor="password">
            {esNuevo ? 'Contrasena inicial' : 'Nueva contrasena'}
          </label>
          <input id="password" type="text" className="campo__control" value={datos.password}
            onChange={cambiar('password')} required={esNuevo}
            placeholder={esNuevo ? 'Minimo 8 caracteres' : 'Dejar vacio para no cambiarla'} />
          <p className="tarjeta__meta">
            Se muestra en claro para que puedas comunicarsela a la persona.
          </p>
        </div>

        <div className="campo">
          <label className="campo__etiqueta">
            <input type="checkbox" checked={datos.is_active}
              onChange={(e) => setDatos({ ...datos, is_active: e.target.checked })}
              style={{ marginRight: 8 }} />
            Cuenta activa
          </label>
          <p className="tarjeta__meta">
            Las cuentas se desactivan, no se borran: asi se conserva quien registro cada cosa.
          </p>
        </div>

        <div className="barra-acciones" style={{ marginTop: 20 }}>
          <button type="submit" className="boton boton--primario" disabled={guardar.isPending}>
            {guardar.isPending ? 'Guardando…' : 'Guardar'}
          </button>
          <button type="button" className="boton boton--texto" onClick={onCerrar}>
            Cancelar
          </button>
        </div>
      </form>
    </Panel>
  )
}

export default function PaginaUsuarios() {
  const { esSuperAdmin } = useAuth()
  const { data: usuarios = [], isLoading, error } = useUsuarios()
  const resetear = useResetearPassword()
  const [editando, setEditando] = useState(null)
  const [temporal, setTemporal] = useState(null)

  const resetearDe = (usuario) => {
    resetear.mutate(usuario.id, {
      onSuccess: (datos) =>
        setTemporal({ username: usuario.username, password: datos.password_temporal }),
    })
  }

  if (error) return <div className="aviso aviso--error">{mensajeDeError(error)}</div>

  return (
    <>
      <p className="antetitulo">Administracion</p>
      <h1 className="titulo-pagina">Usuarios</h1>
      <p className="subtitulo">
        {esSuperAdmin
          ? 'Alta, edicion y restablecimiento de contrasenas.'
          : 'Consulta de cuentas. Solo el super administrador puede modificarlas.'}
      </p>

      {temporal && (
        <div className="aviso aviso--info">
          Contrasena temporal de <strong>{temporal.username}</strong>:{' '}
          <code style={{ fontSize: 15 }}>{temporal.password}</code>
          <br />
          Anotala ahora: no se vuelve a mostrar.
          <button type="button" className="boton boton--texto" onClick={() => setTemporal(null)}>
            Entendido
          </button>
        </div>
      )}

      {esSuperAdmin && (
        <div className="barra-acciones">
          <button type="button" className="boton boton--primario"
            onClick={() => setEditando({})}>
            Nueva cuenta
          </button>
        </div>
      )}

      {isLoading && <p className="cargando">Cargando usuarios…</p>}

      <div style={{ display: 'grid', gap: 8 }}>
        {usuarios.map((u) => (
          <article key={u.id} className="ficha" style={{ gridTemplateColumns: '1fr auto' }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>
                {u.nombre_completo || u.username}
                {!u.is_active && (
                  <span className="distintivo distintivo--categoria" style={{ marginLeft: 8 }}>
                    Inactiva
                  </span>
                )}
              </div>
              <div className="ficha__pie">
                <span className="distintivo distintivo--proceso">{ROLES[u.rol] ?? u.rol}</span>
                {u.region_nombre && (
                  <span className="distintivo distintivo--categoria">{u.region_nombre}</span>
                )}
                <span className="tarjeta__meta">
                  {u.username}
                  {' · '}
                  {u.ultimo_acceso
                    ? `Ultimo acceso ${fechaHora(u.ultimo_acceso)}`
                    : 'Nunca ha entrado'}
                </span>
              </div>
            </div>

            {esSuperAdmin && (
              <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                <button type="button" className="boton boton--texto"
                  onClick={() => setEditando(u)}>
                  Editar
                </button>
                <button type="button" className="boton boton--texto"
                  onClick={() => resetearDe(u)} disabled={resetear.isPending}>
                  Restablecer contrasena
                </button>
              </div>
            )}
          </article>
        ))}
      </div>

      {editando && (
        <FormularioUsuario usuario={editando} onCerrar={() => setEditando(null)} />
      )}
    </>
  )
}
