/**
 * Deterministic layered auto-layout (no external dependency).
 *
 * Roots = nodes with no incoming edges (clients/ingress). Depth = longest
 * path from any root. Nodes are placed in columns by depth, stacked within
 * a column by stable id order so output is reproducible.
 */

interface Positioned {
  id: string
  position: { x: number; y: number }
}

const COL_WIDTH = 260
const ROW_HEIGHT = 120

export function autoLayout<T extends Positioned>(
  nodes: T[],
  edges: { source: string; target: string }[],
): T[] {
  if (nodes.length === 0) return nodes

  const ids = new Set(nodes.map((n) => n.id))
  const outgoing = new Map<string, string[]>()
  const incomingCount = new Map<string, number>()
  for (const id of ids) {
    outgoing.set(id, [])
    incomingCount.set(id, 0)
  }
  for (const e of edges) {
    if (!ids.has(e.source) || !ids.has(e.target)) continue
    outgoing.get(e.source)!.push(e.target)
    incomingCount.set(e.target, (incomingCount.get(e.target) ?? 0) + 1)
  }

  // Longest-path depth via repeated relaxation (graphs are small).
  const depth = new Map<string, number>()
  for (const id of ids) depth.set(id, 0)
  for (let iter = 0; iter < nodes.length; iter++) {
    let changed = false
    for (const [src, dsts] of outgoing) {
      for (const dst of dsts) {
        const candidate = (depth.get(src) ?? 0) + 1
        if ((depth.get(dst) ?? 0) < candidate) {
          // Cycle guard: cap depth at node count to keep layout finite.
          depth.set(dst, Math.min(candidate, nodes.length))
          changed = true
        }
      }
    }
    if (!changed) break
  }

  const byDepth = new Map<number, string[]>()
  for (const node of [...nodes].sort((a, b) => a.id.localeCompare(b.id))) {
    const d = Math.min(depth.get(node.id) ?? 0, maxColumn(nodes.length))
    const list = byDepth.get(d) ?? []
    list.push(node.id)
    byDepth.set(d, list)
  }

  const positions = new Map<string, { x: number; y: number }>()
  for (const [d, list] of [...byDepth.entries()].sort((a, b) => a[0] - b[0])) {
    list.forEach((id, row) => {
      positions.set(id, { x: d * COL_WIDTH, y: row * ROW_HEIGHT })
    })
  }

  return nodes.map((n) => ({
    ...n,
    position: positions.get(n.id) ?? n.position,
  }))
}

function maxColumn(count: number): number {
  return Math.max(0, count - 1)
}
