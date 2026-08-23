/**
 * Canonical ArchitectureGraph adapter.
 *
 * The canvas (React Flow) is a VIEW. This module is the one place that
 * converts view state into the canonical, schema-validated graph shape
 * (schemas/architecture.schema.json). Never the reverse dependency:
 * business logic must never import React Flow types (SYSTEM.md P1).
 *
 * TODO(Phase 2): replace ad-hoc mapping with generated TS types from
 * `src/types/generated/` once the codegen pipeline lands in CI.
 */

export type TrafficType = 'sync_request' | 'async_event' | 'replication' | 'batch'
export type EdgeDirection = 'unidirectional' | 'bidirectional'

/** Minimal structural subset of React Flow node/edge we depend on. */
interface FlowNodeLike {
  id: string
  position: { x: number; y: number }
  data?: Record<string, unknown>
}

interface FlowEdgeLike {
  id: string
  source: string
  target: string
  data?: Record<string, unknown>
}

export interface CanonicalArchitectureNode {
  id: string
  type: string
  name: string
  technology: string | null
  position: { x: number; y: number }
  properties: Record<string, unknown>
  capacity: Record<string, unknown>
  availability: Record<string, unknown>
  deployment: Record<string, unknown>
  metadata: Record<string, unknown>
}

export interface CanonicalArchitectureEdge {
  id: string
  source: string
  target: string
  direction: EdgeDirection
  protocol: string | null
  traffic_type: TrafficType
  properties: Record<string, unknown>
}

export interface CanonicalArchitectureGraph {
  id: string
  version: number
  nodes: CanonicalArchitectureNode[]
  edges: CanonicalArchitectureEdge[]
  groups: unknown[]
  requirements: unknown[]
  constraints: unknown[]
  traffic_model: Record<string, unknown>
  deployment_model: Record<string, unknown>
  metadata: Record<string, unknown>
}

const TRAFFIC_TYPES: readonly TrafficType[] = [
  'sync_request',
  'async_event',
  'replication',
  'batch',
]

export function inferTrafficType(data: Record<string, unknown> | undefined): TrafficType {
  const candidate = data?.['traffic_type']
  if (typeof candidate === 'string' && (TRAFFIC_TYPES as readonly string[]).includes(candidate)) {
    return candidate as TrafficType
  }
  return 'sync_request'
}

function getString(data: Record<string, unknown> | undefined, key: string): string | null {
  const value = data?.[key]
  return typeof value === 'string' ? value : null
}

function getObject(data: Record<string, unknown> | undefined, key: string): Record<string, unknown> {
  const value = data?.[key]
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

export function toArchitectureNode(node: FlowNodeLike): CanonicalArchitectureNode {
  const { data } = node
  return {
    id: node.id,
    type: typeof data?.componentType === 'string' ? data.componentType : 'unknown',
    name: typeof data?.label === 'string' ? data.label : node.id,
    technology: getString(data, 'technology'),
    position: { x: node.position.x, y: node.position.y },
    properties: getObject(data, 'properties'),
    capacity: getObject(data, 'capacity'),
    availability: getObject(data, 'availability'),
    deployment: getObject(data, 'deployment'),
    metadata: getObject(data, 'metadata'),
  }
}

export function toArchitectureEdge(edge: FlowEdgeLike): CanonicalArchitectureEdge {
  const { data } = edge
  return {
    id: edge.id,
    source: edge.source,
    target: edge.target,
    direction: data?.direction === 'bidirectional' ? 'bidirectional' : 'unidirectional',
    protocol: getString(data, 'protocol'),
    traffic_type: inferTrafficType(data),
    properties: getObject(data, 'properties'),
  }
}

export function toArchitectureGraph(input: {
  id: string
  version: number
  nodes: FlowNodeLike[]
  edges: FlowEdgeLike[]
  metadata?: Record<string, unknown>
  trafficModel?: Record<string, unknown>
}): CanonicalArchitectureGraph {
  return {
    id: input.id,
    version: input.version,
    nodes: input.nodes.map(toArchitectureNode),
    edges: input.edges.map(toArchitectureEdge),
    groups: [],
    requirements: [],
    constraints: [],
    traffic_model: input.trafficModel ?? {},
    deployment_model: {},
    metadata: input.metadata ?? {},
  }
}
