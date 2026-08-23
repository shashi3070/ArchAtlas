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
