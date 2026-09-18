import axios from 'axios'

const ALMACEN_REFRESH = 'focos_refresh'

/** El access token vive solo en memoria; el refresh sobrevive a recargas. */
let accessToken = null

export const guardarSesion = ({ access, refresh }) => {
  accessToken = access
  if (refresh) {
    try {
      localStorage.setItem(ALMACEN_REFRESH, refresh)
    } catch {
      /* Modo privado o almacenamiento bloqueado: la sesion durara lo que la pestana. */
    }
  }
}

export const leerRefresh = () => {
  try {
    return localStorage.getItem(ALMACEN_REFRESH)
  } catch {
    return null
  }
}

export const borrarSesion = () => {
  accessToken = null
  try {
    localStorage.removeItem(ALMACEN_REFRESH)
  } catch {
    /* sin almacenamiento: nada que limpiar */
  }
}

export const hayAccessToken = () => Boolean(accessToken)

const cliente = axios.create({ baseURL: '/api' })

cliente.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

/** Renovacion del access ante un 401, reintentando la peticion UNA sola vez. */
let renovacionEnCurso = null

cliente.interceptors.response.use(
  (respuesta) => respuesta,
  async (error) => {
    const original = error.config
    const esNoAutorizado = error.response?.status === 401
    const esRutaDeAuth = original?.url?.includes('/auth/login/')
      || original?.url?.includes('/auth/refresh/')

    if (!esNoAutorizado || original?._reintentado || esRutaDeAuth) {
      return Promise.reject(error)
    }

    const refresh = leerRefresh()
    if (!refresh) return Promise.reject(error)

    original._reintentado = true
    try {
      // Si llegan varios 401 a la vez, todos esperan la misma renovacion.
      renovacionEnCurso = renovacionEnCurso
        || axios.post('/api/auth/refresh/', { refresh })
      const { data } = await renovacionEnCurso
      renovacionEnCurso = null
      guardarSesion({ access: data.access, refresh: data.refresh })
      original.headers.Authorization = `Bearer ${data.access}`
      return cliente(original)
    } catch (fallo) {
      renovacionEnCurso = null
      borrarSesion()
      return Promise.reject(fallo)
    }
  },
)

/** Extrae un mensaje legible del error que devuelve la API. */
export const mensajeDeError = (error, respaldo = 'Ocurrio un error inesperado.') => {
  const datos = error?.response?.data
  if (!datos) return error?.message || respaldo
  if (typeof datos === 'string') return datos
  if (datos.detalle) return datos.detalle
  if (datos.detail) return datos.detail
  const primero = Object.values(datos)[0]
  if (Array.isArray(primero)) return primero[0]
  return typeof primero === 'string' ? primero : respaldo
}

export default cliente
