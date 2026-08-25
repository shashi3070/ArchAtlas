import { useEffect, useState } from 'react'

import {
  simulationApi,
  type NodeSimulationResult,
  type SimulationResult,
  type TrafficModel,
} from '../api/simulation'
import { SimResultsTable } from '../components/simulation/SimResultsTable'
import { TraceView } from '../components/simulation/TraceView'
import { toArchitectureGraph, type CanonicalArchitectureGraph } from '../graph/toArchitectureGraph'
import { useLab } from '../state/labStore'

export function SimulatePage() {
  const nodes = useLab((s) => s.nodes)
  const edges = useLab((s) => s.edges)
  const archId = useLab((s) => s.archId)
  const storeTraffic = useLab((s) => s.trafficModel)

  const [result, setResult] = useState<SimulationResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const [traffic, setTraffic] = useState<TrafficModel>({
    total_rps: storeTraffic.rps ?? 1000,
    read_ratio: storeTraffic.readRatio ?? 0.8,
    write_ratio: 1 - (storeTraffic.readRatio ?? 0.8),
    avg_request_bytes: 2048,
    avg_response_bytes: 8192,
  })

  // Node name map for trace view
  const nodeNameMap: Record<string, string> = {}
  for (const n of nodes) {
    nodeNameMap[n.id] = n.data.label || n.id
  }

  const buildGraph = (): CanonicalArchitectureGraph => {
    const trafficModel: Record<string, unknown> = {}
    if (traffic.total_rps > 0) trafficModel.rps = traffic.total_rps
    if (traffic.read_ratio != null) trafficModel.read_ratio = traffic.read_ratio
    return toArchitectureGraph({
      id: archId ?? `lab-${Date.now()}`,
      version: 1,
      nodes,
      edges,
      metadata: { source: 'simulate' },
      trafficModel,
    })
  }

  const runSimulation = async () => {
    if (nodes.length === 0) {
      setError('No nodes on canvas — add some components first in the Lab.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const graph = buildGraph()
      const res = await simulationApi.run({
        graph_json: graph as unknown as Record<string, unknown>,
        traffic,
      })
      setResult(res)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  // Auto-simulate on mount when graph has nodes
  useEffect(() => {
    if (nodes.length > 0 && !result && !busy) {
      void runSimulation()
    }
  }, [])

  const selectedResult: NodeSimulationResult | null = selectedNode
    ? result?.nodes.find((n) => n.node_id === selectedNode) ?? null
    : null

  return (
    <div className="simulate-page">
      <header className="page-header">
        <h2>Simulation</h2>
        <p className="muted">
          Analytical traffic simulation — capacity, latency, and cost estimates for your architecture
        </p>
      </header>

      {nodes.length === 0 ? (
        <div className="sim-empty">
          <p>No components on the canvas. Head to the <strong>Lab</strong> to build your architecture first.</p>
          <a href="/lab" className="btn primary">Open Lab</a>
        </div>
      ) : (
        <>
          <div className="sim-toolbar">
            <div className="sim-input-group">
              <label>
                Total RPS
                <input
                  type="number"
                  value={traffic.total_rps}
                  onChange={(e) => setTraffic({ ...traffic, total_rps: Number(e.target.value) || 0 })}
                  min={1}
                  style={{ width: 100, marginLeft: 6 }}
                />
              </label>
              <label>
                Read %
                <input
                  type="number"
                  value={Math.round((traffic.read_ratio ?? 0.8) * 100)}
                  onChange={(e) => {
                    const r = Number(e.target.value) / 100
                    setTraffic({ ...traffic, read_ratio: r, write_ratio: 1 - r })
                  }}
                  min={0}
                  max={100}
                  style={{ width: 60, marginLeft: 6 }}
                />
              </label>
              <label>
                Req bytes
                <input
                  type="number"
                  value={traffic.avg_request_bytes}
                  onChange={(e) => setTraffic({ ...traffic, avg_request_bytes: Number(e.target.value) || 512 })}
                  min={64}
                  style={{ width: 80, marginLeft: 6 }}
                />
              </label>
              <label>
                Resp bytes
                <input
                  type="number"
                  value={traffic.avg_response_bytes}
                  onChange={(e) => setTraffic({ ...traffic, avg_response_bytes: Number(e.target.value) || 1024 })}
                  min={64}
                  style={{ width: 80, marginLeft: 6 }}
                />
              </label>
            </div>
            <button
              type="button"
              className="btn primary"
              disabled={busy}
              onClick={() => void runSimulation()}
            >
              {busy ? 'Simulating…' : 'Run Simulation'}
            </button>
          </div>

          {error && <div className="eval-error">{error}</div>}

          {result && (
            <>
              <div className="sim-summary">
                <div className="sim-card">
                  <span className="sim-card-label">End-to-end P95</span>
                  <span className="sim-card-value">{result.summary.end_to_end.p95_ms.toFixed(1)} ms</span>
                </div>
                <div className="sim-card">
                  <span className="sim-card-label">End-to-end P99</span>
                  <span className="sim-card-value">{result.summary.end_to_end.p99_ms.toFixed(1)} ms</span>
                </div>
                <div className="sim-card">
                  <span className="sim-card-label">Monthly cost</span>
                  <span className="sim-card-value">${result.summary.total_cost.total_usd_per_month.toFixed(0)}/mo</span>
                </div>
                <div className="sim-card">
                  <span className="sim-card-label">Effective RPS</span>
                  <span className="sim-card-value">{result.summary.effective_rps.toLocaleString()}</span>
                </div>
                {result.summary.bottleneck_node && (
                  <div className="sim-card sim-card-warn">
                    <span className="sim-card-label">Bottleneck</span>
                    <span className="sim-card-value">
                      {nodeNameMap[result.summary.bottleneck_node] ?? result.summary.bottleneck_node}
                    </span>
                  </div>
                )}
              </div>

              {result.summary.warnings.length > 0 && (
                <div className="sim-warnings">
                  {result.summary.warnings.map((w, i) => (
                    <div key={i} className="eval-error">
                      {w}
                    </div>
                  ))}
                </div>
              )}

              <h3>Node Results</h3>
              <SimResultsTable
                nodes={result.nodes}
                onSelect={setSelectedNode}
                selectedNodeId={selectedNode}
              />

              {selectedResult && (
                <div className="sim-detail">
                  <h3>{selectedResult.name}</h3>
                  <div className="sim-detail-grid">
                    <div>
                      <span className="muted small">Type</span>
                      <span>{selectedResult.node_type}</span>
                    </div>
                    <div>
                      <span className="muted small">Capacity</span>
                      <span>{selectedResult.capacity_rps.toLocaleString()} RPS</span>
                    </div>
                    <div>
                      <span className="muted small">Offered</span>
                      <span>{selectedResult.offered_rps.toLocaleString()} RPS</span>
                    </div>
                    <div>
                      <span className="muted small">Utilization</span>
                      <span>
                        {(selectedResult.utilization.total_utilization * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div>
                      <span className="muted small">P50 / P95 / P99</span>
                      <span>
                        {selectedResult.latency.p50_ms.toFixed(1)} / {selectedResult.latency.p95_ms.toFixed(1)} /{' '}
                        {selectedResult.latency.p99_ms.toFixed(1)} ms
                      </span>
                    </div>
                    <div>
                      <span className="muted small">Error rate</span>
                      <span>{(selectedResult.error_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="muted small">Queue depth</span>
                      <span>{selectedResult.queue_depth.toFixed(1)}</span>
                    </div>
                    <div>
                      <span className="muted small">Cost</span>
                      <span>${selectedResult.cost.usd_per_month.toFixed(0)}/mo</span>
                    </div>
                  </div>
                  {selectedResult.warnings.length > 0 && (
                    <div className="sim-node-warnings">
                      {selectedResult.warnings.map((w, i) => (
                        <div key={i} className="eval-error">
                          {w}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {result.trace_paths.length > 0 && (
                <div className="sim-traces">
                  <h3>Trace Paths</h3>
                  <TraceView traces={result.trace_paths} nodeNameMap={nodeNameMap} />
                </div>
              )}

              {Object.keys(result.summary.total_cost.per_node_usd_per_month).length > 0 && (
                <div className="sim-cost-breakdown">
                  <h3>Cost Breakdown</h3>
                  <div className="sim-cost-grid">
                    {Object.entries(result.summary.total_cost.per_node_usd_per_month)
                      .sort(([, a], [, b]) => b - a)
                      .map(([nodeId, cost]) => (
                        <div key={nodeId} className="sim-cost-row">
                          <span className="sim-cost-name">{nodeNameMap[nodeId] ?? nodeId}</span>
                          <div className="sim-cost-bar-wrap">
                            <div
                              className="sim-cost-bar"
                              style={{
                                width: `${(cost / result.summary.total_cost.total_usd_per_month) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="sim-cost-val">${cost.toFixed(0)}/mo</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
