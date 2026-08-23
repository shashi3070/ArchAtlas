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
