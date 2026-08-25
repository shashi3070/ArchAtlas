import { useState } from 'react'
import type { NodeSimulationResult } from '../../api/simulation'

interface Props {
  nodes: NodeSimulationResult[]
  onSelect?: (nodeId: string | null) => void
  selectedNodeId?: string | null
}

export function SimResultsTable({ nodes, onSelect, selectedNodeId }: Props) {
  const [sortBy, setSortBy] = useState<'utilization' | 'latency' | 'cost' | 'offered_rps'>('utilization')
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc')

  const sorted = [...nodes].sort((a, b) => {
    const dir = sortDir === 'desc' ? -1 : 1
    switch (sortBy) {
      case 'utilization':
        return (a.utilization.total_utilization - b.utilization.total_utilization) * dir
      case 'latency':
        return (a.latency.p95_ms - b.latency.p95_ms) * dir
      case 'cost':
        return (a.cost.usd_per_month - b.cost.usd_per_month) * dir
      case 'offered_rps':
        return (a.offered_rps - b.offered_rps) * dir
    }
  })

  const toggleSort = (col: typeof sortBy) => {
    if (sortBy === col) setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))
    else {
      setSortBy(col)
      setSortDir('desc')
    }
  }

  const sortIndicator = (col: typeof sortBy) =>
    sortBy === col ? (sortDir === 'desc' ? ' ↓' : ' ↑') : ''

  return (
    <div className="sim-table-wrap">
      <table className="sim-table">
        <thead>
          <tr>
            <th>Node</th>
            <th>Type</th>
            <th className="num" onClick={() => toggleSort('offered_rps')}>
              RPS{sortIndicator('offered_rps')}
            </th>
            <th className="num" onClick={() => toggleSort('utilization')}>
              Utilization{sortIndicator('utilization')}
            </th>
            <th className="num" onClick={() => toggleSort('latency')}>
              P95 Latency{sortIndicator('latency')}
            </th>
            <th className="num">P99</th>
            <th className="num">Errors</th>
            <th className="num" onClick={() => toggleSort('cost')}>
              $/mo{sortIndicator('cost')}
            </th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((n) => {
            const util = n.utilization.total_utilization
            const rowClass =
              n.is_bottleneck
                ? 'sim-row-bottleneck'
                : util > 0.8
                  ? 'sim-row-warning'
                  : ''
            return (
              <tr
                key={n.node_id}
                className={`${rowClass}${selectedNodeId === n.node_id ? ' sim-row-selected' : ''}`}
                onClick={() => onSelect?.(selectedNodeId === n.node_id ? null : n.node_id)}
                style={{ cursor: onSelect ? 'pointer' : undefined }}
              >
                <td className="sim-name">{n.name}</td>
                <td className="sim-type">{n.node_type}</td>
                <td className="num">{n.offered_rps.toLocaleString()}</td>
                <td className="num">
                  <span className="util-bar">
                    <span
                      className="util-fill"
                      style={{
                        width: `${Math.min(util * 100, 100)}%`,
                        backgroundColor:
                          util > 1 ? '#ef4444' : util > 0.8 ? '#f59e0b' : '#22c55e',
                      }}
                    />
                  </span>
                  {(util * 100).toFixed(1)}%
                </td>
                <td className="num">{n.latency.p95_ms.toFixed(1)} ms</td>
                <td className="num">{n.latency.p99_ms.toFixed(1)} ms</td>
                <td className="num">
                  {n.error_rate > 0 ? (
                    <span className="sim-error">{(n.error_rate * 100).toFixed(1)}%</span>
                  ) : (
                    <span className="sim-ok">0%</span>
                  )}
                </td>
                <td className="num">${n.cost.usd_per_month.toFixed(0)}</td>
                <td>
                  {n.warnings.length > 0 && (
                    <span className="sim-status-chip" title={n.warnings.join('\n')}>
                      {n.is_bottleneck ? '🔴' : util > 0.8 ? '🟡' : '🟢'}
                    </span>
                  )}
                  {n.warnings.length === 0 && <span className="sim-ok">OK</span>}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
