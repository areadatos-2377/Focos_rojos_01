import { useEffect, useState } from 'react'

/**
 * Pantalla de arranque (Fase 0). Sirve para confirmar que el frontend habla con
 * el backend a traves del proxy de Vite. Se reemplaza en la Fase 3.
 */
export default function App() {
  const [estado, setEstado] = useState({ cargando: true })

  useEffect(() => {
    fetch('/api/salud/')
      .then((r) => r.json())
      .then((datos) => setEstado({ cargando: false, ok: datos.estado === 'ok' }))
      .catch((error) => setEstado({ cargando: false, ok: false, error: String(error) }))
  }, [])

  return (
    <main style={{ maxWidth: 680, margin: '0 auto', padding: '64px 24px' }}>
      <p style={{
        font: '600 12px/1 var(--fuente-texto)', letterSpacing: '.14em',
        textTransform: 'uppercase', color: 'var(--dorado-pale-tx)', margin: 0,
      }}>
        IMSS-Bienestar
      </p>
      <h1 style={{ fontSize: 40, margin: '8px 0 4px', color: 'var(--verde-d)' }}>
        Reporte Focos Rojos
      </h1>
      <p style={{ color: 'var(--gray-tx)', margin: '0 0 32px' }}>
        Registro y seguimiento de situaciones por entidad.
      </p>

      <div style={{
        background: 'var(--paper)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', padding: 20,
        borderLeft: '4px solid var(--verde)',
      }}>
        <strong style={{ display: 'block', marginBottom: 6 }}>Estado del sistema</strong>
        {estado.cargando && <span style={{ color: 'var(--gray-tx)' }}>Consultando…</span>}
        {!estado.cargando && estado.ok && (
          <span style={{ color: 'var(--verde)' }}>
            Backend conectado. Base de datos y catalogos listos.
          </span>
        )}
        {!estado.cargando && !estado.ok && (
          <span style={{ color: 'var(--alerta-pale-tx)' }}>
            Sin respuesta del backend. {estado.error}
          </span>
        )}
      </div>
    </main>
  )
}
