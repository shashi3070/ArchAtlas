import { api } from './client'
import type { CanonicalArchitectureGraph } from '../graph/toArchitectureGraph'

export interface AgentReply {
  task: string
  source: 'llm' | 'deterministic'
  text: string
  cache_hit: boolean
}

export interface AgentProposalAddNode {
  ref: string
  component_type: string
  name?: string | null
  replicas?: number
}

export interface AgentProposalConnect {
  source_ref: string
  target_ref: string
  traffic_type?: string
}

export interface AgentProposalSetProperties {
  match_component_type: string
  properties?: Record<string, unknown>
  availability?: Record<string, unknown>
}

export interface AgentProposal {
  summary: string
  add_nodes: AgentProposalAddNode[]
  connect: AgentProposalConnect[]
  set_properties: AgentProposalSetProperties[]
  remove_node_ids: string[]
}

export interface ProposalReply {
  task: string
  proposal: AgentProposal
  raw: string
  cache_hit: boolean
}

export const agentApi = {
  explain: (result: unknown) => api.post<AgentReply>('/api/agent/explain', { result }),
  critique: (graph: CanonicalArchitectureGraph) =>
    api.post<AgentReply>('/api/agent/critique', { graph }),
  proposal: (graph: CanonicalArchitectureGraph, goal: string) =>
    api.post<ProposalReply>('/api/agent/proposal', { graph, goal }),
}
