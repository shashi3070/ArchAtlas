import type { DeltaReport } from '../../api/chaos'

interface Props {
  delta: DeltaReport
  nodeNameMap?: Record<string, string>
}

function MetricRow({ label, before, after, unit, better }: {
  label: string
  before: number
  after: number
  unit: string
  better: 'higher' | 'lower'
}) {
  const diff = after - before
  const improved = better === 'lower' ? diff < 0 : diff > 0
  const degraded = better === 'lower' ? diff > 0 : diff < 0
  const unchanged = Math.abs(diff) < 0.01

  return (
    <tr className={degraded ? 'chaos-degraded' : improved ? 'chaos-improved' : ''}>
      <td className="chaos-metric-label">{label}</td>
      <td className="num">{before.toFixed(1)}{unit}</td>
      <td className="num">
        {after.toFixed(1)}{unit}
        {!unchanged && (
          <span className={degraded ? 'chaos-arrow-bad' : 'chaos-arrow-good'}>
            {degraded ? ' ▲' : ' ▼'}
          </span>
        )}
      </td>
      <td className="num">
        {!unchanged && (
          <span className={degraded ? 'chaos-diff-bad' : 'chaos-diff-good'}>
            {diff > 0 ? '+' : ''}{diff.toFixed(1)}{unit}
          </span>
        )}
      </td>
    </tr>
  )
}

export function DeltaReportView({ delta, nodeNameMap }: Props) {
  const nameMap = nodeNameMap ?? {}
  return (
    <div className="chaos-delta">
      <table className="chaos-delta-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th className="num">Before</th>
            <th className="num">After</th>
            <th className="num">Delta</th>
          </tr>
        </thead>
        <tbody>
          <MetricRow
            label="Availability"
            before={delta.availability_before}
            after={delta.availability_after}
            unit="%"
            better="higher"
          />
          <MetricRow
            label="P95 Latency"
            before={delta.latency_p95_before}
            after={delta.latency_p95_after}
            unit="ms"
            better="lower"
          />
          <MetricRow
            label="Monthly Cost"
            before={delta.cost_before}
            after={delta.cost_after}
            unit="$"
            better="lower"
          />
        </tbody>
      </table>

      {delta.overloaded_nodes_after.length > 0 && (
        <div className="chaos-overloaded">
          <strong>Newly overloaded nodes:</strong>{' '}
          {delta.overloaded_nodes_after.map((id) => nameMap[id] ?? id).join(', ')}
        </div>
      )}

      {delta.bottleneck_after && delta.bottleneck_after !== delta.bottleneck_before && (
        <div className="chaos-bottleneck-shift">
          <strong>Bottleneck shifted:</strong>{' '}
          {nameMap[delta.bottleneck_before ?? ''] ?? delta.bottleneck_before ?? 'none'} →{' '}
          {nameMap[delta.bottleneck_after] ?? delta.bottleneck_after}
        </div>
      )}

      <div className="chaos-root-cause">
        <h4>Root Cause</h4>
        <p>{delta.root_cause}</p>
      </div>

      <div className="chaos-mitigation">
        <h4>Suggested Mitigation</h4>
        <p>{delta.mitigation}</p>
      </div>
    </div>
  )
}
