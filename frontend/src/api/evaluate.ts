import { api } from './client'
import type { CanonicalArchitectureGraph } from '../graph/toArchitectureGraph'

export type RuleStatus = 'PASS' | 'WARNING' | 'FAIL' | 'INFO' | 'UNKNOWN'

export interface DimensionScore {
  dimension: string
  score: number
  status: string
}

export interface SuggestedAction {
  action: string
  tradeoffs?: string[]
}

export interface RuleResult {
  rule_id: string
  status: RuleStatus
  message: string
  severity?: string
  evidence?: string[]
  affected_nodes?: string[]
  affected_edges?: string[]
  requirement_ids?: string[]
  confidence?: 'high' | 'medium' | 'low'
  confidence_reason?: string
  suggested_actions?: SuggestedAction[]
}

export interface SpofEntry {
  node_id: string
  blast_radius: string
  reason: string
}

export interface BottleneckEntry {
  node_id: string
  demand: number
  capacity: number
  unit: string
  path: string[]
  reason: string
}

export interface RequirementOutcome {
  requirement_id: string
  status: 'satisfied' | 'at_risk' | 'violated' | 'not_evaluable'
  confidence: 'high' | 'medium' | 'low'
  reason?: string | null
  evidence?: string[]
}

export interface Recommendation {
  problem: string
  evidence: string[]
  recommendation: string
  expected_benefit: string
  tradeoffs?: string[]
  confidence: string
  alternatives?: string[]
}

export interface EvaluationMetrics {
  demand_rps_estimated: number | null
  read_rps_estimated: number | null
  write_rps_estimated: number | null
  read_demand_basis: string
  cache_inline: boolean
  node_count: number
  edge_count: number
}

export interface EvaluationResult {
  architecture_id: string | null
  architecture_version: number
  rule_version: string
  evaluated_at?: string
  summary: {
    overall_status: 'pass' | 'warning' | 'fail'
    dimension_scores: DimensionScore[]
  }
  rule_results: RuleResult[]
  bottlenecks: BottleneckEntry[]
  spofs: SpofEntry[]
  requirement_outcomes: RequirementOutcome[]
  recommendations: Recommendation[]
  metrics: EvaluationMetrics
}

export const evaluateApi = {
  evaluate: (graph: CanonicalArchitectureGraph, architectureId?: string | null) =>
    api.post<EvaluationResult>('/api/evaluate', {
      graph,
      architecture_id: architectureId ?? null,
    }),
}
