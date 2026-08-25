import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { collaborateApi, type SharedArchitecture } from '../api/collaborate'

export function SharedPage() {
  const { token } = useParams<{ token: string }>()
  const [data, setData] = useState<SharedArchitecture | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(true)

  useEffect(() => {
    if (!token) return
    setBusy(true)
    collaborateApi
      .getShared(token)
      .then(setData)
      .catch((e) => setError((e as Error).message))
      .finally(() => setBusy(false))
  }, [token])

  if (busy) return <div className="sim-empty"><p>Loading shared architecture…</p></div>
  if (error) return <div className="sim-empty"><p className="eval-error">{error}</p></div>
  if (!data) return null

  const graph = data.graph as Record<string, unknown>
  const nodes = (graph.nodes ?? []) as Record<string, unknown>[]
  const edges = (graph.edges ?? []) as Record<string, unknown>[]

  return (
    <div className="shared-page">
      <header className="page-header">
        <h2>{data.name}</h2>
        <p className="muted">
          Shared architecture · version {data.current_version} · updated{' '}
          {new Date(data.updated_at).toLocaleDateString()}
        </p>
      </header>

      <div className="shared-graph-info">
        <div className="sim-summary">
          <div className="sim-card">
            <span className="sim-card-label">Components</span>
            <span className="sim-card-value">{nodes.length}</span>
          </div>
          <div className="sim-card">
            <span className="sim-card-label">Connections</span>
            <span className="sim-card-value">{edges.length}</span>
          </div>
        </div>

        <div className="shared-nodes">
          <h3>Components</h3>
          <div className="shared-node-list">
            {(nodes as Record<string, unknown>[]).map((n, i) => (
              <div key={i} className="shared-node-item">
                <span className="shared-node-name">{String(n.name ?? n.id)}</span>
                <span className="shared-node-type muted">{String(n.type)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="shared-edges">
          <h3>Connections</h3>
          <div className="shared-edge-list">
            {(edges as Record<string, unknown>[]).map((e, i) => (
              <div key={i} className="shared-edge-item">
                <span>{String(e.source)}</span>
                <span className="muted">→</span>
                <span>{String(e.target)}</span>
                <span className="shared-edge-type muted">{String(e.traffic_type)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
