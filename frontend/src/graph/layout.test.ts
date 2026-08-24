import { describe, expect, it } from 'vitest'

import { autoLayout } from './layout'

describe('autoLayout', () => {
  const nodes = [
    { id: 'client', position: { x: 0, y: 0 } },
    { id: 'api', position: { x: 999, y: 999 } },
    { id: 'db', position: { x: 999, y: 999 } },
  ]
  const chain = [
    { source: 'client', target: 'api' },
    { source: 'api', target: 'db' },
  ]

  it('stacks levels vertically: roots on top, downstream below', () => {
    const out = autoLayout(nodes, chain)
    const byId = new Map(out.map((n) => [n.id, n.position]))
    expect(byId.get('client')!.y).toBeLessThan(byId.get('api')!.y)
    expect(byId.get('api')!.y).toBeLessThan(byId.get('db')!.y)
  })

  it('places same-level nodes on the same row (equal y)', () => {
    const wide = [
      { id: 'client', position: { x: 0, y: 0 } },
      { id: 'apiA', position: { x: 9, y: 9 } },
      { id: 'apiB', position: { x: 5, y: 5 } },
      { id: 'db', position: { x: 1, y: 2 } },
    ]
    const fanOut = [
      { source: 'client', target: 'apiA' },
      { source: 'client', target: 'apiB' },
      { source: 'apiA', target: 'db' },
      { source: 'apiB', target: 'db' },
    ]
    const out = autoLayout(wide, fanOut)
    const byId = new Map(out.map((n) => [n.id, n.position]))
    expect(byId.get('apiA')!.y).toBe(byId.get('apiB')!.y)
    // A node only appears BELOW all of its inputs.
    expect(byId.get('client')!.y).toBeLessThan(byId.get('apiA')!.y)
    expect(byId.get('db')!.y).toBeGreaterThan(byId.get('apiB')!.y)
  })

  it('orders each row to reduce crossings (barycenter)', () => {
    const grid = [
      { id: 'r1', position: { x: 0, y: 0 } },
      { id: 'r2', position: { x: 0, y: 0 } },
      { id: 'a1', position: { x: 0, y: 0 } },
      { id: 'a2', position: { x: 0, y: 0 } },
    ]
    const cross = [
      { source: 'r1', target: 'a1' },
      { source: 'r1', target: 'a2' },
      { source: 'r2', target: 'a2' },
    ]
    const out = autoLayout(grid, cross)
    const byId = new Map(out.map((n) => [n.id, n.position]))
    // a1's only parent r1 sits left of a2's parents {r1,r2} average.
    expect(byId.get('a1')!.x).toBeLessThan(byId.get('a2')!.x)
    expect(byId.get('a1')!.y).toBe(byId.get('a2')!.y)
  })

  it('is deterministic for identical input', () => {
    const two = [
      { id: 'b', position: { x: 5, y: 5 } },
      { id: 'a', position: { x: 1, y: 1 } },
    ]
    expect(autoLayout(two, [{ source: 'a', target: 'b' }])).toEqual(
      autoLayout(two, [{ source: 'a', target: 'b' }]),
    )
  })

  it('handles cycles and dangling edges without hanging', () => {
    const cyc = [
      { id: 'x', position: { x: 0, y: 0 } },
      { id: 'y', position: { x: 0, y: 0 } },
    ]
    const loopEdges = [
      { source: 'x', target: 'y' },
      { source: 'y', target: 'x' },
      { source: 'ghost', target: 'x' },
    ]
    const out = autoLayout(cyc, loopEdges)
    expect(out).toHaveLength(2)
  })

  it('returns empty input untouched', () => {
    expect(autoLayout([], [])).toEqual([])
  })
})
