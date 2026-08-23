import { describe, expect, it } from 'vitest'

import { autoLayout } from './layout'

describe('autoLayout', () => {
  it('places roots in column 0 and downstream nodes to the right', () => {
    const nodes = [
      { id: 'client', position: { x: 0, y: 0 } },
      { id: 'api', position: { x: 999, y: 999 } },
      { id: 'db', position: { x: 999, y: 999 } },
    ]
    const edges = [
      { source: 'client', target: 'api' },
      { source: 'api', target: 'db' },
    ]
    const out = autoLayout(nodes, edges)
    const byId = new Map(out.map((n) => [n.id, n.position]))
    expect(byId.get('client')!.x).toBeLessThan(byId.get('api')!.x)
    expect(byId.get('api')!.x).toBeLessThan(byId.get('db')!.x)
  })

  it('is deterministic for identical input', () => {
    const nodes = [
      { id: 'b', position: { x: 5, y: 5 } },
      { id: 'a', position: { x: 1, y: 1 } },
    ]
    const edges = [{ source: 'a', target: 'b' }]
    expect(autoLayout(nodes, edges)).toEqual(autoLayout(nodes, edges))
  })

  it('handles cycles and dangling edges without hanging', () => {
    const nodes = [
      { id: 'x', position: { x: 0, y: 0 } },
      { id: 'y', position: { x: 0, y: 0 } },
    ]
    const edges = [
      { source: 'x', target: 'y' },
      { source: 'y', target: 'x' },
      { source: 'ghost', target: 'x' },
    ]
    const out = autoLayout(nodes, edges)
    expect(out).toHaveLength(2)
  })

  it('returns empty input untouched', () => {
    expect(autoLayout([], [])).toEqual([])
  })
})
