import { useLab } from '../../state/labStore'
import { markerForDirection } from '../../graph/fromArchitectureGraph'

const TRAFFIC_TYPES = ['sync_request', 'async_event', 'replication', 'batch'] as const
const DIRECTIONS = ['unidirectional', 'bidirectional'] as const

export function EdgeInspector() {
  const edges = useLab((s) => s.edges)
  const selectedEdgeId = useLab((s) => s.selectedEdgeId)
  const commit = useLab((s) => s.commit)

  const edge = edges.find((e) => e.id === selectedEdgeId)
  if (!edge) return null

  const setField = (key: 'traffic_type' | 'direction' | 'protocol', value: string) =>
    commit(({ edges: eds }) => {
      const target = eds.find((e) => e.id === edge.id)
      if (target) {
        ;(target.data as Record<string, unknown>)[key] =
          key === 'protocol' ? (value === '' ? null : value) : value
        if (key === 'direction') {
          // Keep the on-canvas arrowhead in sync with the direction field.
          target.markerEnd = markerForDirection(
            value as 'unidirectional' | 'bidirectional',
          )
        }
      }
    })

  return (
    <aside className="inspector" aria-label="edge properties">
      <h3>Connection</h3>
      <p className="muted small">
        {edge.source} → {edge.target}
      </p>

      <label className="field">
        Traffic type
        <select
          value={edge.data.traffic_type}
          onChange={(e) => setField('traffic_type', e.target.value)}
        >
          {TRAFFIC_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        Direction
        <select
          value={edge.data.direction}
          onChange={(e) => setField('direction', e.target.value)}
        >
          {DIRECTIONS.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        Protocol
        <input
          type="text"
          placeholder="http, grpc, tcp…"
          value={edge.data.protocol ?? ''}
          onChange={(e) => setField('protocol', e.target.value)}
        />
      </label>

      <button
        type="button"
        className="btn ghost small-btn"
        onClick={() =>
          commit(({ edges: eds }) => {
            const idx = eds.findIndex((e) => e.id === edge.id)
            if (idx >= 0) eds.splice(idx, 1)
          })
        }
      >
        Delete connection
      </button>
    </aside>
  )
}
