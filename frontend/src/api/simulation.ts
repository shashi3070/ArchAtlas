/**
 * Simulation API client — typed fetch wrappers for /api/simulate endpoints.
 */

export interface TrafficModel {
  total_rps: number
  read_ratio?: number
  write_ratio?: number
  avg_request_bytes?: number
  avg_response_bytes?: number
  avg_data_record_bytes?: number
  think_time_ms?: number
}

export interface NodeOverrides {
  node_id: string
  replicas?: number
  cache_hit_ratio?: number
  properties?: Record<string, unknown>
}

export interface SimulationInput {
  graph_json: Record<string, unknown>
  traffic: TrafficModel
  node_overrides?: NodeOverrides[]
}

export interface NodeUtilization {
  read_utilization: number
  write_utilization: number
  total_utilization: number
}

export interface NodeLatency {
  p50_ms: number
  p95_ms: number
  p99_ms: number
  base_ms: number
}

export interface NodeCost {
  usd_per_month: number
  usd_per_request: number
}

export interface NodeSimulationResult {
  node_id: string
  node_type: string
  name: string
  capacity_rps: number
  offered_rps: number
  routed_rps: number
  utilization: NodeUtilization
  latency: NodeLatency
  cost: NodeCost
  error_rate: number
  queue_depth: number
  is_bottleneck: boolean
  warnings: string[]
}

export interface EdgeFlow {
  rps: number
  bandwidth_mbps: number
  saturation: number
}

export interface EdgeSimulationResult {
  edge_id: string
  source: string
  target: string
  traffic_type: string
  flow: EdgeFlow
  warnings: string[]
}

export interface PercentileEstimate {
  p50_ms: number
  p95_ms: number
  p99_ms: number
}

export interface CostBreakdown {
  total_usd_per_month: number
  per_node_usd_per_month: Record<string, number>
}

export interface SimulationSummary {
  total_rps: number
  effective_rps: number
  end_to_end: PercentileEstimate
  total_cost: CostBreakdown
  bottleneck_node: string | null
  overloaded_nodes: string[]
  warnings: string[]
}

export interface SimulationResult {
  input_hash: string
  nodes: NodeSimulationResult[]
  edges: EdgeSimulationResult[]
  trace_paths: TracePath[]
  summary: SimulationSummary
  timestamp: string
}

export interface TrafficHop {
  node_id: string
  node_type: string
  latency_ms: number
  cache_hit: boolean
  queued: boolean
}

export interface TracePath {
  path_nodes: string[]
  total_latency_ms: number
  hops: TrafficHop[]
}

export interface SimulationRun {
  id: string
  owner_key: string
  created_at: string
  architecture_id: string | null
  architecture_version: number | null
  graph_hash: string
  traffic_rps: number
  input_json: Record<string, unknown>
  result_json: Record<string, unknown>
  result_summary: string
}

const BASE = '/api/simulate'

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status} ${text}`)
  }
  return res.json() as Promise<T>
}

export const simulationApi = {
  run: (input: SimulationInput) =>
    api<SimulationResult>('', {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  quick: (graph_json: Record<string, unknown>, total_rps: number = 1000) =>
    api<SimulationResult>('/quick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(graph_json),
      ...(() => {
        const url = new URL(`${BASE}/quick`, window.location.origin)
        url.searchParams.set('total_rps', String(total_rps))
        return { url: url.toString() }
      })(),
    }),

  listRuns: () => api<SimulationRun[]>(''),

  getRun: (run_id: string) => api<SimulationRun>(`/${run_id}`),
}
