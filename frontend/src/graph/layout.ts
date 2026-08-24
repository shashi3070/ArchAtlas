/**
 * Deterministic layered auto-layout, vertical top-to-bottom.
 *
 * Level 0 = nodes with no incoming edges (clients/ingress). A node's level
 * is its longest-path distance from any root, so every node sits on the
 * first row where ALL of its inputs have already appeared - which is what
 * makes same-level siblings share one horizontal row.
 *
 * Within a row, nodes are ordered by barycenter (average x of their
 * predecessors from earlier rows) to reduce edge crossings; ties fall back
 * to stable id order so output is reproducible.
 */

interface Positioned {
  id: string
  position: { x: number }
}

const COL_WIDTH = 220
const ROW_HEIGHT = 150

export function autoLayout<T extends Positioned>(
  nodes: T[],
  edges: { source: string; target: string }[],
): T[] {
  if (nodes.length === 0) return nodes

  const ids = new Set(nodes.map((n) => n.id))
  const outgoing = new Map<string, string[]>()
  const incoming = new Map<string, string[]>()
  for (const id of ids) {
    outgoing.set(id, [])
    incoming.set(id, [])
  }
  for (const e of edges) {
    if (!ids.has(e.source) || !ids.has(e.target)) continue
    if (e.source === e.target) continue
    outgoing.get(e.source)!.push(e.target)
    incoming.get(e.target)!.push(e.source)
  }

  // Longest-path level via repeated relaxation (graphs are small).
  const level = new Map<string, number>()
  for (const id of ids) level.set(id, 0)
  for (let iter = 0; iter < nodes.length; iter++) {
    let changed = false
    for (const [src, dsts] of outgoing) {
      for (const dst of dsts) {
        const candidate = (level.get(src) ?? 0) + 1
        if ((level.get(dst) ?? 0) < candidate) {
          // Cycle guard: cap at node count so relaxation always terminates.
          level.set(dst, Math.min(candidate, nodes.length))
          changed = true
        }
      }
    }
    if (!changed) break
  }

  const rows = new Map<number, string[]>()
  for (const node of [...nodes].sort((a, b) => a.id.localeCompare(b.id))) {
    const d = Math.min(level.get(node.id) ?? 0, Math.max(0, nodes.length - 1))
    const list = rows.get(d) ?? []
    list.push(node.id)
    rows.set(d, list)
  }

  const positions = new Map<string, { x: number; y: number }>()
  const sortedLevels = [...rows.keys()].sort((a, b) => a - b)
  const widestRow = Math.max(
    ...sortedLevels.map((d) => rows.get(d)!.length),
  )
  const centerX = ((widestRow - 1) / 2) * COL_WIDTH

  for (const d of sortedLevels) {
    const list = rows.get(d)!
    // Barycenter ordering against already-placed predecessors.
    if (d > 0) {
      const score = new Map<string, number>()
      for (const id of list) {
        const preds = incoming.get(id)!.filter((p) => positions.has(p))
        score.set(
          id,
          preds.length === 0
            ? Number.MAX_SAFE_INTEGER // push source-less nodes to the row's end
            : preds.reduce((sum, p) => sum + positions.get(p)!.x, 0) / preds.length,
        )
      }
      list.sort(
        (a, b) => score.get(a)! - score.get(b)! || a.localeCompare(b),
      )
    }
    list.forEach((id, col) => {
      positions.set(id, {
        x: centerX + (col - (list.length - 1) / 2) * COL_WIDTH,
        y: d * ROW_HEIGHT,
      })
    })
  }

  return nodes.map((n) => ({
    ...n,
    position: positions.get(n.id) ?? n.position,
  }))
}
