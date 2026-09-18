import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import './estilos/base.css'
import './estilos/app.css'
import App from './App.jsx'
import { ProveedorAuth } from './contextos/AuthContext'

const clienteConsultas = new QueryClient({
  defaultOptions: {
    queries: {
      // Un 401 lo resuelve el interceptor renovando el token; reintentar aqui
      // solo duplicaria peticiones.
      retry: (intentos, error) =>
        error?.response?.status !== 401 && error?.response?.status !== 404 && intentos < 2,
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={clienteConsultas}>
        <ProveedorAuth>
          <App />
        </ProveedorAuth>
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
