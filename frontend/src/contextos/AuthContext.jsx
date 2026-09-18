import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import cliente, { borrarSesion, guardarSesion, leerRefresh } from '../api/cliente'

const AuthContext = createContext(null)

export function ProveedorAuth({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(true)

  /** Al abrir la app, intenta recuperar la sesion con el refresh guardado. */
  useEffect(() => {
    const refresh = leerRefresh()
    if (!refresh) {
      setCargando(false)
      return
    }
    axios
      .post('/api/auth/refresh/', { refresh })
      .then(({ data }) => {
        guardarSesion({ access: data.access, refresh: data.refresh || refresh })
        return cliente.get('/auth/yo/')
      })
      .then(({ data }) => setUsuario(data))
      .catch(() => borrarSesion())
      .finally(() => setCargando(false))
  }, [])

  const entrar = useCallback(async (username, password) => {
    const { data } = await axios.post('/api/auth/login/', { username, password })
    guardarSesion({ access: data.access, refresh: data.refresh })
    setUsuario(data.usuario)
    return data.usuario
  }, [])

  const salir = useCallback(async () => {
    const refresh = leerRefresh()
    if (refresh) {
      try {
        await cliente.post('/auth/logout/', { refresh })
      } catch {
        /* El token pudo expirar solo; la sesion local se cierra igual. */
      }
    }
    borrarSesion()
    setUsuario(null)
  }, [])

  const valor = useMemo(
    () => ({
      usuario,
      cargando,
      entrar,
      salir,
      autenticado: Boolean(usuario),
      esAdmin: usuario?.rol === 'ADMINISTRADOR' || usuario?.rol === 'SUPER_ADMIN',
      esSuperAdmin: usuario?.rol === 'SUPER_ADMIN',
    }),
    [usuario, cargando, entrar, salir],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (contexto === null) {
    throw new Error('useAuth debe usarse dentro de <ProveedorAuth>.')
  }
  return contexto
}
