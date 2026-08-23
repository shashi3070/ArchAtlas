import { api } from './client'
import type { CanonicalArchitectureGraph } from '../graph/toArchitectureGraph'

export interface ArchitectureMeta {
  id: string
  name: string
  current_version: number
  challenge_id: string | null
  updated_at: string
}

export interface VersionMeta {
  version: number
  note: string
  created_at: string
  is_current: boolean
}

export const architecturesApi = {
  create: (name: string, graph: CanonicalArchitectureGraph, challengeId?: string) =>
    api.post<ArchitectureMeta>('/api/architectures', {
      name,
      graph,
      challenge_id: challengeId ?? null,
    }),

  list: () => api.get<ArchitectureMeta[]>('/api/architectures'),

  get: (id: string) =>
    api.get<ArchitectureMeta & { graph: CanonicalArchitectureGraph }>(
      `/api/architectures/${id}`,
    ),

  update: (id: string, graph: CanonicalArchitectureGraph, note = '') =>
    api.put<ArchitectureMeta>(`/api/architectures/${id}`, { graph, note }),

  versions: (id: string) => api.get<VersionMeta[]>(`/api/architectures/${id}/versions`),

  versionGraph: (id: string, version: number) =>
    api.post<{ version: number; note: string; graph: CanonicalArchitectureGraph }>(
      `/api/architectures/${id}/versions/${version}`,
      {},
    ),

  restore: (id: string, version: number) =>
    api.post<ArchitectureMeta>(`/api/architectures/${id}/restore`, { version }),
}
