/**
 * Reverse adapter: canonical ArchitectureGraph -> React Flow view state.
 * The mirror of toArchitectureGraph; still the only bridge between the
 * canonical document and the canvas.
 */

import type { CanonicalArchitectureEdge, CanonicalArchitectureGraph, CanonicalArchitectureNode } from './toArchitectureGraph'

export interface LabNode {
  id: string
  type: 'component'
  position: { x: number; y: number }
  data: {
    label: string
    componentType: string
    technology?: string | null
    capacity?: Record<string, unknown>
    availability?: Record<string, unknown>
    deployment?: Record<string, unknown>
    properties?: Record<string, unknown>
  }
}

export interface LabEdge {
  id: string
  source: string
  target: string
  animated?: boolean
  label?: string
  data: {
    traffic_type: CanonicalArchitectureEdge['traffic_type']
    direction: CanonicalArchitectureEdge['direction']
    protocol: string | null
  }
}

export function fromArchitectureNode(node: CanonicalArchitectureNode): LabNode {
  return {
    id: node.id,
    type: 'component',
    position: { x: node.position.x, y: node.position.y },
    data: {
      label: node.name,
      componentType: node.type,
      technology: node.technology ?? null,
      capacity: node.capacity ?? {},
      availability: node.availability ?? {},
      deployment: node.deployment ?? {},
      properties: node.properties ?? {},
    },
  }
}

export function fromArchitectureEdge(edge: CanonicalArchitectureEdge): LabEdge {
  return {
    id: edge.id,
    source: edge.source,
    target: edge.target,
    animated: edge.traffic_type === 'async_event' || edge.traffic_type === 'batch',
    label:
      edge.traffic_type === 'async_event'
        ? 'async'
        : edge.traffic_type === 'replication'
          ? 'repl'
          : undefined,
    data: {
      traffic_type: edge.traffic_type,
      direction: edge.direction,
      protocol: edge.protocol ?? null,
    },
  }
}

export function fromArchitectureGraph(graph: CanonicalArchitectureGraph): {
  nodes: LabNode[]
  edges: LabEdge[]
} {
  const known = new Set(graph.nodes.map((n) => n.id))
  return {
    nodes: graph.nodes.map(fromArchitectureNode),
    // Drop dangling edges defensively rather than corrupting the view.
    edges: graph.edges
      .filter((e) => known.has(e.source) && known.has(e.target))
      .map(fromArchitectureEdge),
  }
}
