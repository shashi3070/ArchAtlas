export interface ChaosEvent {
  id: string
  name: string
  description: string
  affected_node_types: string[]
  transform: Record<string, unknown>
  expected_effect: string
}

export interface DeltaReport {
  availability_before: number
  availability_after: number
  latency_p95_before: number
  latency_p95_after: number
  cost_before: number
  cost_after: number
  error_rate_before: number
  error_rate_after: number
  overloaded_nodes_before: string[]
  overloaded_nodes_after: string[]
  bottleneck_before: string | null
  bottleneck_after: string | null
  root_cause: string
  mitigation: string
}

export interface EventOutcome {
  event_id: string
  event_name: string
  affected_node_ids: string[]
  before_summary: Record<string, unknown>
  after_summary: Record<string, unknown>
  delta: Record<string, unknown>
  severity: string
}

export interface ChaosRunResult {
  event_id: string
  event_name: string
  before_simulation: Record<string, unknown>
  after_simulation: Record<string, unknown>
  delta_report: DeltaReport
  outcomes: EventOutcome[]
  timestamp: string
}

const BASE = '/api/chaos'

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

export const chaosApi = {
  listEvents: () => api<ChaosEvent[]>('/events'),
  getEvent: (id: string) => api<ChaosEvent>(`/events/${id}`),
  runChaos: (graph_json: Record<string, unknown>, event_id: string, traffic_rps?: number) =>
    api<ChaosRunResult>('/run', {
      method: 'POST',
      body: JSON.stringify({ graph_json, event_id, traffic_rps }),
    }),
}
