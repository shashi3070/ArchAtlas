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

export interface ChatMessageInput {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatReply {
  task: string
  reply: string
  suggest?: string[]
  fix: AgentProposal
  raw: string
  cache_hit: boolean
}

export interface ProviderInfo {
  id: string
  label: string
  requires_key: boolean
  key_present: boolean
  default_model: string
  active: boolean
}

export interface ProvidersReply {
  active: string
  providers: ProviderInfo[]
}

/** Result of applying a proposal onto the canvas. */
export interface ApplyReport {
  applied: number
  skipped: string[]
}

export interface ProviderModelsReply {
  provider: string
  models: string[]
  default_model: string
  error: string | null
}

export const agentApi = {
  explain: (result: unknown) => api.post<AgentReply>('/api/agent/explain', { result }),
  critique: (graph: CanonicalArchitectureGraph) =>
    api.post<AgentReply>('/api/agent/critique', { graph }),
  proposal: (graph: CanonicalArchitectureGraph, goal: string) =>
    api.post<ProposalReply>('/api/agent/proposal', { graph, goal }),
  providers: () => api.get<ProvidersReply>('/api/agent/providers'),
  models: (providerId: string) =>
    api.get<ProviderModelsReply>(
      `/api/agent/models?provider=${encodeURIComponent(providerId)}`,
    ),
  chat: (
    graph: CanonicalArchitectureGraph,
    messages: ChatMessageInput[],
    providerId: string,
    goal = '',
    model = '',
  ) =>
    api.post<ChatReply>('/api/agent/chat', {
      graph,
      messages,
      provider_id: providerId,
      goal,
      model,
    }),
}
