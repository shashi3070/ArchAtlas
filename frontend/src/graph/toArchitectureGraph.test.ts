import { describe, expect, it } from 'vitest'

import { inferTrafficType, toArchitectureGraph } from './toArchitectureGraph'

const nodes = [
  {
    id: 'client-1',
    position: { x: 10, y: 20 },
    data: { label: 'Web Client', componentType: 'client' },
  },
  {
    id: 'api-1',
    position: { x: 200, y: 20 },
    data: {
      label: 'API',
      componentType: 'api',
      capacity: { rps_per_instance: 2000 },
    },
  },
]

const edges = [{ id: 'e1', source: 'client-1', target: 'api-1' }]

describe('toArchitectureGraph', () => {
  it('maps view state to the canonical graph envelope', () => {
    const graph = toArchitectureGraph({ id: 'g1', version: 3, nodes, edges })
    expect(graph.id).toBe('g1')
    expect(graph.version).toBe(3)
    expect(graph.nodes).toHaveLength(2)
    expect(graph.edges).toHaveLength(1)
    expect(graph.groups).toEqual([])
    expect(graph.requirements).toEqual([])
    expect(graph.constraints).toEqual([])
  })

  it('maps node fields with defaults for missing data', () => {
    const [node] = toArchitectureGraph({ id: 'g', version: 1, nodes, edges: [] }).nodes
    expect(node.id).toBe('client-1')
    expect(node.type).toBe('client')
    expect(node.name).toBe('Web Client')
    expect(node.position).toEqual({ x: 10, y: 20 })
    expect(node.technology).toBeNull()
    expect(node.properties).toEqual({})
  })

  it('preserves node capacity overrides', () => {
    const [, apiNode] = toArchitectureGraph({ id: 'g', version: 1, nodes, edges: [] }).nodes
    expect(apiNode.capacity).toEqual({ rps_per_instance: 2000 })
  })

  it('defaults edge traffic_type to sync_request', () => {
    const [edge] = toArchitectureGraph({ id: 'g', version: 1, nodes, edges }).edges
    expect(edge.traffic_type).toBe('sync_request')
    expect(edge.direction).toBe('unidirectional')
    expect(edge.protocol).toBeNull()
  })

  it('respects explicit async_event override', () => {
    const asyncEdges = [
      {
        id: 'e2',
        source: 'api-1',
        target: 'client-1',
        data: { traffic_type: 'async_event', protocol: 'amqp' },
      },
    ]
    const [edge] = toArchitectureGraph({ id: 'g', version: 1, nodes, edges: asyncEdges }).edges
    expect(edge.traffic_type).toBe('async_event')
    expect(edge.protocol).toBe('amqp')
  })
})

describe('inferTrafficType', () => {
  it('falls back to sync_request on unknown values', () => {
    expect(inferTrafficType(undefined)).toBe('sync_request')
    expect(inferTrafficType({ traffic_type: 'carrier_pigeon' })).toBe('sync_request')
    expect(inferTrafficType({ traffic_type: 'replication' })).toBe('replication')
  })
})
