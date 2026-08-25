import { useEffect, useState } from 'react'

import { chaosApi, type ChaosEvent, type ChaosRunResult } from '../api/chaos'
import { toArchitectureGraph } from '../graph/toArchitectureGraph'
import { useLab } from '../state/labStore'
import { DeltaReportView } from '../components/chaos/DeltaReportView'

export function ChaosPage() {
  const nodes = useLab((s) => s.nodes)
  const edges = useLab((s) => s.edges)
  const archId = useLab((s) => s.archId)
  const trafficModel = useLab((s) => s.trafficModel)

  const [events, setEvents] = useState<ChaosEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<string>('')
  const [result, setResult] = useState<ChaosRunResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const nodeNameMap: Record<string, string> = {}
  for (const n of nodes) {
    nodeNameMap[n.id] = n.data.label || n.id
  }

  useEffect(() => {
    chaosApi.listEvents().then(setEvents).catch(() => {})
  }, [])

  const runChaos = async () => {
    if (!selectedEvent) {
      setError('Select a chaos event first.')
      return
    }
    if (nodes.length === 0) {
      setError('No nodes on canvas — build an architecture in the Lab first.')
      return
    }

    setBusy(true)
    setError(null)
    try {
      const trafficModelDict: Record<string, unknown> = {}
      if (trafficModel.rps != null) trafficModelDict.rps = trafficModel.rps
      if (trafficModel.readRatio != null) trafficModelDict.read_ratio = trafficModel.readRatio

      const graph = toArchitectureGraph({
        id: archId ?? `chaos-${Date.now()}`,
        version: 1,
        nodes,
        edges,
        metadata: { source: 'chaos' },
        trafficModel: trafficModelDict,
      })

      const res = await chaosApi.runChaos(
        graph as unknown as Record<string, unknown>,
        selectedEvent,
        trafficModel.rps ?? undefined,
      )
      setResult(res)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const selectedEventDef = events.find((e) => e.id === selectedEvent)

  return (
    <div className="chaos-page">
      <header className="page-header">
        <h2>Chaos Engineering</h2>
        <p className="muted">
          Inject failures, observe consequences, and learn how architectures behave under stress
        </p>
      </header>

      {nodes.length === 0 ? (
        <div className="sim-empty">
          <p>No architecture on canvas. Build one in the <strong>Lab</strong> first.</p>
          <a href="/lab" className="btn primary">Open Lab</a>
        </div>
      ) : (
        <>
          <div className="chaos-toolbar">
            <div className="chaos-event-grid">
              {events.map((ev) => (
                <button
                  key={ev.id}
                  type="button"
                  className={`chaos-event-card${selectedEvent === ev.id ? ' chaos-event-selected' : ''}`}
                  onClick={() => {
                    setSelectedEvent(ev.id)
                    setResult(null)
                  }}
                >
                  <span className="chaos-event-name">{ev.name}</span>
                  <span className="chaos-event-desc muted small">{ev.description}</span>
                </button>
              ))}
            </div>

            {selectedEventDef && (
              <div className="chaos-event-detail">
                <h4>{selectedEventDef.name}</h4>
                <p className="muted small">{selectedEventDef.expected_effect}</p>
                <p className="muted small">
                  Affected types: {selectedEventDef.affected_node_types.join(', ')}
                </p>
              </div>
            )}

            <button
              type="button"
              className="btn primary"
              disabled={busy || !selectedEvent}
              onClick={() => void runChaos()}
            >
              {busy ? 'Injecting…' : '▶ Run Chaos Scenario'}
            </button>
          </div>

          {error && <div className="eval-error">{error}</div>}

          {result && (
            <div className="chaos-result">
              <div className="chaos-severity-bar">
                <span className={`chaos-severity chaos-severity-${result.outcomes[0]?.severity ?? 'low'}`}>
                  {(result.outcomes[0]?.severity ?? 'unknown').toUpperCase()}
                </span>
                <span className="muted">{result.event_name}</span>
              </div>

              <DeltaReportView delta={result.delta_report} nodeNameMap={nodeNameMap} />

              {result.outcomes[0] && result.outcomes[0].affected_node_ids.length > 0 && (
                <div className="chaos-affected">
                  <h4>Affected Nodes</h4>
                  <ul>
                    {result.outcomes[0].affected_node_ids.map((id) => (
                      <li key={id}>{nodeNameMap[id] ?? id}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
