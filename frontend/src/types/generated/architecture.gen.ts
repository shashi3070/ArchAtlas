/**
 * The canonical, machine-readable system model. The canvas is only a view of this graph.
 */
export interface ArchitectureGraph {
  id: string;
  /**
   * Immutable architecture versions increment this counter.
   */
  version: number;
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
  /**
   * Visual/logical groupings of nodes (trust boundaries, tiers).
   */
  groups?: ArchitectureGroup[];
  requirements?: Requirement[];
  constraints?: Constraint[];
  traffic_model?: TrafficModel;
  deployment_model?: DeploymentModel;
  /**
   * Provenance: author, challenge_id, created_at, labels. Never used by evaluators for correctness.
   */
  metadata?: {
    [k: string]: unknown;
  };
}
/**
 * A component instance in the canonical architecture graph. Position is presentation-only; evaluators must be position-insensitive.
 */
export interface ArchitectureNode {
  id: string;
  /**
   * Component catalog type (e.g. 'redis', 'load_balancer'). Must exist in the versioned component catalog.
   */
  type: string;
  name: string;
  /**
   * Optional concrete technology label distinct from the abstract type.
   */
  technology?: string | null;
  position: {
    x: number;
    y: number;
  };
  /**
   * Component-specific configuration (replicas, cache pattern, ttl, partition key...).
   */
  properties?: {
    [k: string]: unknown;
  };
  /**
   * Effective capacity overrides for this instance; falls back to catalog capacity_defaults.
   */
  capacity?: {
    [k: string]: unknown;
  };
  /**
   * Availability configuration: replicas, multi_az, multi_region, failover mode.
   */
  availability?: {
    [k: string]: unknown;
  };
  /**
   * Deployment placement: region, az, environment.
   */
  deployment?: {
    [k: string]: unknown;
  };
  metadata?: {
    [k: string]: unknown;
  };
}
/**
 * A typed directed connection between two nodes. Evaluation-relevant edges must carry traffic_type and direction semantics.
 */
export interface ArchitectureEdge {
  id: string;
  /**
   * Id of the source ArchitectureNode.
   */
  source: string;
  /**
   * Id of the target ArchitectureNode.
   */
  target: string;
  /**
   * Flow direction semantics. Defaults to unidirectional source->target.
   */
  direction?: "unidirectional" | "bidirectional";
  /**
   * Optional protocol label (http, grpc, tcp, amqp, native...).
   */
  protocol?: string | null;
  /**
   * Semantic traffic classification used by the evaluator.
   */
  traffic_type?: "sync_request" | "async_event" | "replication" | "batch";
  /**
   * Edge semantics: pattern (sync|async), delivery (at_most_once|at_least_once|exactly_once), ordering, throughput hints, read/write ratio.
   */
  properties?: {
    [k: string]: unknown;
  };
}
export interface ArchitectureGroup {
  id: string;
  name: string;
  node_ids?: string[];
  properties?: {
    [k: string]: unknown;
  };
}
/**
 * A machine-checkable requirement the architecture must satisfy. RuleResults map onto requirement ids.
 */
export interface Requirement {
  id: string;
  category:
    "functional" | "scale" | "performance" | "availability" | "consistency" | "durability" | "security" | "cost";
  description: string;
  /**
   * Numeric target or symbolic target (e.g. 'strong', 'global'). Null for purely functional statements.
   */
  target?: number | string | null;
  /**
   * Unit of the target (rps, ms, percent, usd_per_month, ...).
   */
  unit?: string | null;
  /**
   * Weight used by scoring aggregation.
   */
  priority?: "must" | "should" | "could";
  /**
   * Machine-checkable expressions, e.g. 'rps >= 100000', 'p95 <= 200ms', 'availability >= 99.99'.
   */
  validation_rules?: string[];
}
/**
 * A constraint bounding the solution space (budget, residency, consistency class, durability).
 */
export interface Constraint {
  id: string;
  type: "budget" | "data_residency" | "consistency_class" | "durability" | "compliance" | "operational" | "other";
  description: string;
  /**
   * Constraint value (number, string, or structured object).
   */
  value?: {
    [k: string]: unknown;
  };
  /**
   * How binding the constraint is.
   */
  severity?: "hard" | "soft";
  metadata?: {
    [k: string]: unknown;
  };
}
/**
 * Declared workload the architecture must handle.
 */
export interface TrafficModel {
  rps?: number | null;
  read_ratio?: number | null;
  write_ratio?: number | null;
  avg_request_size_bytes?: number | null;
  concurrency?: number | null;
  payload_growth_per_day_bytes?: number | null;
  notes?: string | null;
}
/**
 * Where the system runs: regions, environment, cloud abstraction level.
 */
export interface DeploymentModel {
  environment?: "local" | "staging" | "production";
  regions?: string[];
  multi_az?: boolean | null;
  notes?: string | null;
}
