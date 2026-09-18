import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import cliente from './cliente'

/* --- Catalogos (casi estaticos: se cachean mucho tiempo) --- */

export const useEntidades = () =>
  useQuery({
    queryKey: ['entidades'],
    queryFn: async () => (await cliente.get('/entidades/')).data,
    staleTime: 30 * 60 * 1000,
  })

export const useCategorias = () =>
  useQuery({
    queryKey: ['categorias'],
    queryFn: async () => (await cliente.get('/categorias/')).data,
    staleTime: 10 * 60 * 1000,
  })

export const useCrearCategoria = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (nombre) => (await cliente.post('/categorias/', { nombre })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categorias'] }),
  })
}

/* --- Situaciones --- */

export const clavesSituaciones = (entidadClave, archivadas) =>
  ['situaciones', entidadClave, archivadas ? 'archivadas' : 'activas']

export const useSituaciones = (entidadClave, archivadas = false) =>
  useQuery({
    queryKey: clavesSituaciones(entidadClave, archivadas),
    queryFn: async () => {
      const { data } = await cliente.get('/situaciones/', {
        params: {
          entidad_clave: entidadClave,
          archivadas: archivadas ? 'true' : undefined,
          tamano: 200,
        },
      })
      return data.results ?? data
    },
    enabled: Boolean(entidadClave),
  })

export const useSituacion = (id) =>
  useQuery({
    queryKey: ['situacion', id],
    queryFn: async () => (await cliente.get(`/situaciones/${id}/`)).data,
    enabled: Boolean(id),
  })

export const useBitacora = (id) =>
  useQuery({
    queryKey: ['bitacora', id],
    queryFn: async () => (await cliente.get(`/situaciones/${id}/bitacora/`)).data,
    enabled: Boolean(id),
  })

export const useGuardarSituacion = (entidadClave) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...datos }) =>
      id
        ? (await cliente.patch(`/situaciones/${id}/`, datos)).data
        : (await cliente.post('/situaciones/', datos)).data,
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ['situaciones', entidadClave] })
      qc.invalidateQueries({ queryKey: ['concentrado'] })
      if (variables.id) {
        qc.invalidateQueries({ queryKey: ['situacion', variables.id] })
        qc.invalidateQueries({ queryKey: ['bitacora', variables.id] })
      }
    },
  })
}

export const useCambiarArchivado = (entidadClave) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, accion }) =>
      (await cliente.post(`/situaciones/${id}/${accion}/`)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['situaciones', entidadClave] })
      qc.invalidateQueries({ queryKey: ['concentrado'] })
    },
  })
}

/**
 * Reordenamiento con actualizacion optimista: la ficha se mueve al instante y,
 * si el servidor rechaza el cambio, se restaura el orden anterior.
 */
export const useReordenar = (entidadClave) => {
  const qc = useQueryClient()
  const clave = clavesSituaciones(entidadClave, false)

  return useMutation({
    mutationFn: async (ids) =>
      (await cliente.put(`/entidades/${entidadClave}/orden-situaciones/`, { orden: ids }))
        .data,
    onMutate: async (ids) => {
      await qc.cancelQueries({ queryKey: clave })
      const previas = qc.getQueryData(clave)
      if (previas) {
        const porId = new Map(previas.map((s) => [s.id, s]))
        qc.setQueryData(
          clave,
          ids.map((id, indice) => ({ ...porId.get(id), orden: indice + 1 })),
        )
      }
      return { previas }
    },
    onError: (_error, _ids, contexto) => {
      if (contexto?.previas) qc.setQueryData(clave, contexto.previas)
    },
    onSettled: () => qc.invalidateQueries({ queryKey: clave }),
  })
}

/* --- Administracion --- */

export const useRegiones = () =>
  useQuery({
    queryKey: ['regiones'],
    queryFn: async () => (await cliente.get('/regiones/')).data,
    staleTime: 60 * 60 * 1000,
  })

export const useUsuarios = () =>
  useQuery({
    queryKey: ['usuarios'],
    queryFn: async () => {
      const { data } = await cliente.get('/usuarios/', { params: { tamano: 200 } })
      return data.results ?? data
    },
  })

export const useGuardarUsuario = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...datos }) =>
      id
        ? (await cliente.patch(`/usuarios/${id}/`, datos)).data
        : (await cliente.post('/usuarios/', datos)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['usuarios'] }),
  })
}

export const useResetearPassword = () =>
  useMutation({
    mutationFn: async (id) =>
      (await cliente.post(`/usuarios/${id}/resetear-password/`)).data,
  })

export const useRenombrarCategoria = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, nombre }) =>
      (await cliente.patch(`/categorias/${id}/`, { nombre })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categorias'] }),
  })
}

export const useFusionarCategorias = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, destino }) =>
      (await cliente.post(`/categorias/${id}/fusionar/`, { destino })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['categorias'] })
      qc.invalidateQueries({ queryKey: ['situaciones'] })
    },
  })
}

export const useEliminarCategoria = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id) => (await cliente.delete(`/categorias/${id}/`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categorias'] }),
  })
}

export const useAccesos = (usuarioId) =>
  useQuery({
    queryKey: ['accesos', usuarioId ?? 'todos'],
    queryFn: async () => {
      const { data } = await cliente.get('/auditoria/accesos/', {
        params: { usuario: usuarioId || undefined, tamano: 100 },
      })
      return data.results ?? data
    },
  })
