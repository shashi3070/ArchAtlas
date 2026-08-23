/**
 * A chaos/scenario event definition (Phase 8). Injecting an event transforms a copy of the architecture; the engine then re-evaluates and produces a before/after delta.
 */
export interface ScenarioEvent {
  id: string;
  event_type:
    | "db_failure"
    | "cache_failure"
    | "queue_failure"
    | "region_outage"
    | "network_latency"
    | "traffic_spike"
    | "hot_key"
    | "consumer_lag"
    | "dependency_outage"
    | "hit_ratio_drop"
    | "custom";
  title: string;
  description?: string | null;
  /**
   * Typed parameters per event_type (multiplier for traffic_spike, added_ms for network_latency, new_ratio for hit_ratio_drop, target_component_types...).
   */
  params?: {
    [k: string]: unknown;
  };
  applies_to?: AppliesTo;
  /**
   * Documented expectations used in deterministic scenario fixtures (e.g. availability drops when no failover exists).
   */
  expected_effects?: ExpectedEffect[];
  version?: string;
}
export interface AppliesTo {
  component_types?: string[];
}
export interface ExpectedEffect {
  metric:
    | "availability"
    | "latency_p95"
    | "throughput"
    | "error_rate"
    | "queue_depth"
    | "db_load"
    | "cache_hit_ratio"
    | "cost";
  change: "increase" | "decrease" | "degrade" | "improve" | "none";
  /**
   * Guard expression on architecture state (e.g. 'no_failover', 'single_instance').
   */
  condition?: string | null;
}
