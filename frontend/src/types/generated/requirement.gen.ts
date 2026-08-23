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
