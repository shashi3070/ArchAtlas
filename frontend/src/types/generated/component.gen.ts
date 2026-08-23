/**
 * A versioned catalog entry: identity, machine-readable knowledge block, capacity/cost assumption defaults, and palette presentation. Knowledge lives here - never in React components.
 */
export interface ComponentCatalogEntry {
  type: string;
  category:
    | "client"
    | "edge"
    | "traffic"
    | "compute"
    | "cache"
    | "database"
    | "messaging"
    | "storage"
    | "observability"
    | "reliability"
    | "ai_genai";
  name: string;
  description?: string | null;
  /**
   * Semver of this catalog entry.
   */
  version: string;
  capabilities?: string[];
  /**
   * Problems this component can reduce (e.g. database_read_load).
   */
  helps_with?: string[];
  does_not_solve?: string[];
  /**
   * New concerns introduced by adding this component.
   */
  risks?: string[];
  common_patterns?: string[];
  failure_modes?: string[];
  tradeoffs?: string[];
  /**
   * Assumed per-unit capacities (safe_reads_per_sec, safe_writes_per_sec, rps_per_instance...). Labeled assumptions; overridable per node instance.
   */
  capacity_defaults?: {
    [k: string]: unknown;
  };
  /**
   * Rough monthly cost estimates per unit (usd_per_unit_month). Estimates only.
   */
  cost_defaults?: {
    [k: string]: unknown;
  };
  palette?: PalettePresentation;
}
export interface PalettePresentation {
  group?: string;
  /**
   * Icon identifier string, rendered by the frontend icon layer.
   */
  icon?: string | null;
  color?: string | null;
}
