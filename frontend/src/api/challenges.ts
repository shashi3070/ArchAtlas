import { api } from './client'
import type { CanonicalArchitectureGraph } from '../graph/toArchitectureGraph'
import type { LabEdge, LabNode } from '../graph/fromArchitectureGraph'

export interface ChallengeChainSummary {
  family_id: string | null
  level: number | null
  next_challenge_id: string | null
}

export interface ChallengeSummary {
  id: string
  title: string
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  mode: 'challenge' | 'repair' | 'explore' | 'interview'
  narrative: string | null
  has_starting_graph: boolean
  hint_count: number
  requirement_count: number
  chain: ChallengeChainSummary | null
}

export interface ChallengeRequirement {
  id: string
  category: string
  description: string
  metric?: string
  value?: number
  unit?: string
  priority?: 'must' | 'should' | 'could'
}

export interface ChallengeConstraint {
  key: string
  value: unknown
}

export interface ChallengeDetail {
  id: string
  title: string
  difficulty: ChallengeSummary['difficulty']
  mode: ChallengeSummary['mode']
  narrative?: string
  requirements: ChallengeRequirement[]
  allowed_components?: string[]
  constraints?: ChallengeConstraint[]
  chain?: ChallengeChainSummary
  hint_count: number
  starting_graph?: CanonicalArchitectureGraph
}

export interface HintLadder {
  challenge_id: string
  level: number
  total: number
  hints: string[]
}

export interface ScoredRequirement {
  requirement_id: string
  priority: string
  status: 'satisfied' | 'at_risk' | 'violated' | 'not_evaluable'
  weight: number
  points: number
  reason?: string | null
  confidence?: string | null
}

export interface ScoredFinding {
  rule_id: string
  severity: string
  message: string
}

export interface ScoredSubmission {
  challenge_id: string
  score: number
  passed: boolean
  breakdown: ScoredRequirement[]
  constraint_violations: string[]
  blocking_failure: boolean
  findings: ScoredFinding[]
  spofs: Array<Record<string, unknown>>
  bottlenecks: Array<Record<string, unknown>>
  attempt: number
  evaluated_at: string
}

export interface SubmissionSummary {
  attempt: number
  score: number
  passed: boolean
  created_at: string | null
}

export const challengesApi = {
  list: () => api.get<ChallengeSummary[]>('/api/challenges'),
  get: (cid: string) => api.get<ChallengeDetail>(`/api/challenges/${cid}`),
  hints: (cid: string, level: number) =>
    api.get<HintLadder>(`/api/challenges/${cid}/hints?level=${level}`),
  submit: (cid: string, graph: CanonicalArchitectureGraph) =>
    api.post<ScoredSubmission>(`/api/challenges/${cid}/submit`, { graph }),
  submissions: (cid: string) =>
    api.get<SubmissionSummary[]>(`/api/challenges/${cid}/submissions`),
}

export interface ChallengeDraft {
  nodes: LabNode[]
  edges: LabEdge[]
}
