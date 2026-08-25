import { useState } from 'react'

import { collaborateApi, type CompareResult } from '../api/collaborate'

export function ComparePage() {
  const [archA, setArchA] = useState('')
  const [verA, setVerA] = useState(1)
  const [archB, setArchB] = useState('')
  const [verB, setVerB] = useState(1)
  const [result, setResult] = useState<CompareResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const doCompare = async () => {
    if (!archA || !archB) {
      setError('Enter both architecture IDs.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const res = await collaborateApi.compare(archA, verA, archB, verB)
      setResult(res)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const d = result?.diff

  return (
    <div className="compare-page">
      <header className="page-header">
        <h2>Compare Architectures</h2>
        <p className="muted">Side-by-side structural diff between two architecture versions</p>
      </header>

      <div className="compare-toolbar">
        <div className="compare-input-group">
          <label>
            Architecture A
            <input value={archA} onChange={(e) => setArchA(e.target.value)} placeholder="arch id" />
          </label>
          <label>
            Version
            <input type="number" value={verA} onChange={(e) => setVerA(Number(e.target.value))} min={1} style={{ width: 60 }} />
          </label>
        </div>
        <span className="compare-vs">vs</span>
        <div className="compare-input-group">
          <label>
            Architecture B
            <input value={archB} onChange={(e) => setArchB(e.target.value)} placeholder="arch id" />
          </label>
          <label>
            Version
            <input type="number" value={verB} onChange={(e) => setVerB(Number(e.target.value))} min={1} style={{ width: 60 }} />
          </label>
        </div>
        <button type="button" className="btn primary" disabled={busy} onClick={() => void doCompare()}>
          {busy ? 'Comparing…' : 'Compare'}
        </button>
      </div>

      {error && <div className="eval-error">{error}</div>}

      {d && (
        <div className="compare-result">
          <div className="compare-summary-cards">
            <div className="compare-card">
              <span className="compare-card-label">Nodes Added</span>
              <span className="compare-card-value compare-added">+{d.nodes_added}</span>
            </div>
            <div className="compare-card">
              <span className="compare-card-label">Nodes Removed</span>
              <span className="compare-card-value compare-removed">-{d.nodes_removed}</span>
            </div>
            <div className="compare-card">
              <span className="compare-card-label">Nodes Modified</span>
              <span className="compare-card-value compare-modified">~{d.nodes_modified}</span>
            </div>
            <div className="compare-card">
              <span className="compare-card-label">Edges Added</span>
              <span className="compare-card-value compare-added">+{d.edges_added}</span>
            </div>
            <div className="compare-card">
              <span className="compare-card-label">Edges Removed</span>
              <span className="compare-card-value compare-removed">-{d.edges_removed}</span>
            </div>
            <div className="compare-card">
              <span className="compare-card-label">Edges Modified</span>
              <span className="compare-card-value compare-modified">~{d.edges_modified}</span>
            </div>
          </div>

          {d.details.modified_nodes.length > 0 && (
            <div className="compare-section">
              <h3>Modified Nodes</h3>
              {d.details.modified_nodes.map((m) => (
                <div key={m.id} className="compare-diff-item">
                  <strong>{m.id}</strong>
                  <div className="compare-diff-detail">
                    <span className="compare-before">Before: {JSON.stringify(m.before).slice(0, 120)}…</span>
                    <span className="compare-after">After: {JSON.stringify(m.after).slice(0, 120)}…</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {d.details.added_nodes.length > 0 && (
            <div className="compare-section">
              <h3>Added Nodes</h3>
              {d.details.added_nodes.map((n: Record<string, unknown>, i: number) => (
                <div key={i} className="compare-diff-item compare-added-bg">
                  + {(n as Record<string, string>).name ?? (n as Record<string, string>).id} ({(n as Record<string, string>).type})
                </div>
              ))}
            </div>
          )}

          {d.details.removed_nodes.length > 0 && (
            <div className="compare-section">
              <h3>Removed Nodes</h3>
              {d.details.removed_nodes.map((n: Record<string, unknown>, i: number) => (
                <div key={i} className="compare-diff-item compare-removed-bg">
                  - {(n as Record<string, string>).name ?? (n as Record<string, string>).id} ({(n as Record<string, string>).type})
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
