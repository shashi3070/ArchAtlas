export interface GraphDiff {
  nodes_added: number
  nodes_removed: number
  nodes_modified: number
  edges_added: number
  edges_removed: number
  edges_modified: number
  details: {
    added_nodes: Record<string, unknown>[]
    removed_nodes: Record<string, unknown>[]
    modified_nodes: { id: string; before: Record<string, unknown>; after: Record<string, unknown> }[]
    added_edges: Record<string, unknown>[]
    removed_edges: Record<string, unknown>[]
    modified_edges: { id: string; before: Record<string, unknown>; after: Record<string, unknown> }[]
  }
}

export interface CompareResult {
  arch_a: string
  version_a: number
  arch_b: string
  version_b: number
  diff: GraphDiff
}

export interface SharedArchitecture {
  id: string
  name: string
  current_version: number
  updated_at: string
  graph: Record<string, unknown>
}

const BASE = '/api/architectures'

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const stored = localStorage.getItem('sdp.client_key')
  if (stored) headers['X-Client-Key'] = stored

  const res = await fetch(`${BASE}${path}`, { headers, ...init })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status} ${text}`)
  }
  return res.json() as Promise<T>
}

async function apiPublic<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status} ${text}`)
  }
  return res.json() as Promise<T>
}

export const collaborateApi = {
  share: (arch_id: string) =>
    api<{ share_url: string; share_token: string }>(`/${arch_id}/share`, { method: 'POST' }),

  getShared: (token: string) => apiPublic<SharedArchitecture>(`/api/architectures/shared/${token}`),

  compare: (arch_id_a: string, version_a: number, arch_id_b: string, version_b: number) =>
    api<CompareResult>('/compare', {
      method: 'POST',
      body: JSON.stringify({ arch_id_a, version_a, arch_id_b, version_b }),
    }),

  listVersions: (arch_id: string) =>
    api<{ version: number; note: string; created_at: string; is_current: boolean }[]>(
      `/${arch_id}/versions`,
    ),

  getVersionGraph: (arch_id: string, version: number) =>
    api<{ version: number; note: string; graph: Record<string, unknown> }>(
      `/${arch_id}/versions/${version}`,
      { method: 'POST' },
    ),
}
