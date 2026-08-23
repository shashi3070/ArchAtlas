/**
 * Deterministic, reproducible evaluation output. Same graph + requirements + rule_version must produce identical results.
 */
export interface EvaluationState {
  architecture_id: string;
  architecture_version: number;
  /**
   * Version of the rule pack used; recorded for historical reproducibility.
   */
  rule_version: string;
  component_catalog_version?: string | null;
  challenge_version?: string | null;
  evaluated_at?: string | null;
  summary: EvaluationSummary;
  rule_results: RuleResult[];
  /**
   * Capacity-vs-demand findings on specific nodes/paths.
   */
  bottlenecks?: BottleneckFinding[];
  /**
   * Single points of failure detected on critical paths.
   */
  spofs?: SpofFinding[];
  requirement_outcomes?: RequirementOutcome[];
  recommendations?: Recommendation[];
  /**
   * Free-form computed metrics (estimated rps at each hop, utilization ratios).
   */
  metrics?: {
    [k: string]: unknown;
  };
}
export interface EvaluationSummary {
  overall_status?: "pass" | "warning" | "fail" | "unknown";
  dimension_scores: DimensionScore[];
}
export interface DimensionScore {
  dimension:
    | "functionality"
    | "scalability"
    | "availability"
    | "latency"
    | "consistency"
    | "security"
    | "cost"
    | "observability";
  score: number;
  status?: "pass" | "warning" | "fail" | "info" | "unknown";
}
export interface RuleResult {
  rule_id: string;
  status: "PASS" | "WARNING" | "FAIL" | "INFO" | "UNKNOWN";
  severity?: "critical" | "high" | "medium" | "low";
  message: string;
  /**
   * Concrete facts: numbers, node properties, requirement ids. Never vibes.
   */
  evidence?: string[];
  affected_nodes?: string[];
  affected_edges?: string[];
  requirement_ids?: string[];
  suggested_actions?: SuggestedAction[];
  /**
   * Architectural confidence in this result. LOW/MEDIUM require a stated reason to prevent false precision.
   */
  confidence?: "high" | "medium" | "low";
  confidence_reason?: string | null;
}
export interface SuggestedAction {
  action: string;
  rationale?: string | null;
  tradeoffs?: string[];
  alternatives?: string[];
}
export interface BottleneckFinding {
  node_id: string;
  path?: string[];
  demand?: number | null;
  capacity?: number | null;
  unit?: string | null;
  reason: string;
  severity?: "info" | "warning" | "critical";
}
export interface SpofFinding {
  node_id: string;
  blast_radius?: "total" | "major" | "partial";
  reason: string;
}
export interface RequirementOutcome {
  requirement_id: string;
  status: "satisfied" | "at_risk" | "violated" | "not_evaluable";
  confidence: "high" | "medium" | "low";
  evidence?: string[];
  reason?: string | null;
}
export interface Recommendation {
  problem: string;
  evidence?: string[];
  recommendation: string;
  expected_benefit?: string | null;
  tradeoffs?: string[];
  alternatives?: string[];
  confidence: "high" | "medium" | "low";
  related_topics?: string[];
}
