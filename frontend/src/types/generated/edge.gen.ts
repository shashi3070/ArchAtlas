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
