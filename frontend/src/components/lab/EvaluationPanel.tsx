import { useEffect, useState } from 'react'
import type {
  BottleneckEntry,
  DimensionScore,
  EvaluationResult,
  Recommendation,
  RequirementOutcome,
  RuleResult,
  RuleStatus,
  SpofEntry,
} from '../../api/evaluate'

export interface WorkloadInput {
  rps: number | null
  readRatio: number | null
}

interface EvaluationPanelProps {
  result: EvaluationResult | null
  loading: boolean
  error: string | null
  workload: WorkloadInput
  onClose: () => void
  onEvaluate: (workload: WorkloadInput) => void
}

const STATUS_CLASS: Record<string, string> = {
  pass: 'chip-ok',
  satisfied: 'chip-ok',
  warning: 'chip-warn',
  at_risk: 'chip-warn',
  fail: 'chip-off',
  violated: 'chip-off',
}

function statusClass(status: string): string {
  return STATUS_CLASS[status] ?? ''
}

function statusChip(status: string) {
  return <span className={`chip ${statusClass(status)}`}>{status.replace('_', ' ')}</span>
}

function num(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2)
}

function FindingCard({ finding }: { finding: RuleResult }) {
  const [open, setOpen] = useState(finding.status !== 'PASS')
  const hasDetails =
    (finding.evidence?.length ?? 0) > 0 ||
    (finding.affected_nodes?.length ?? 0) > 0 ||
    (finding.suggested_actions?.length ?? 0) > 0 ||
    !!finding.confidence_reason

  return (
    <div className={`eval-finding eval-finding-${finding.status.toLowerCase()}`}>
      <button type="button" className="eval-finding-head" onClick={() => setOpen(!open)}>
        <span className={`chip ${statusClass(finding.status.toLowerCase())}`}>
          {finding.status}
        </span>
        <span className="eval-rule-id">{finding.rule_id}</span>
        {finding.confidence && finding.confidence !== 'high' && (
          <span className="chip">{finding.confidence} confidence</span>
        )}
      </button>
      <p className="eval-message">{finding.message}</p>
      {open && hasDetails && (
        <div className="eval-details">
          {finding.confidence_reason && (
            <p className="small muted">Why low confidence: {finding.confidence_reason}</p>
          )}
          {!!finding.evidence?.length && (
            <ul className="eval-evidence">
              {finding.evidence.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          )}
          {!!finding.suggested_actions?.length && (
            <div className="eval-actions">
              {finding.suggested_actions.map((a) => (
                <div key={a.action}>
                  <span className="eval-arrow">→</span> {a.action}
                  {!!a.tradeoffs?.length && (
                    <span className="small muted"> (tradeoffs: {a.tradeoffs.join(', ')})</span>
                  )}
                </div>
              ))}
            </div>
          )}
          {!!finding.affected_nodes?.length && (
            <div className="eval-refs">
              {finding.affected_nodes.map((id) => (
                <span key={id} className="chip">
                  {id}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function DimensionBar({ dim }: { dim: DimensionScore }) {
  return (
    <div className="eval-dim">
      <div className="eval-dim-label">
        <span>{dim.dimension}</span>
        <span className={`chip ${statusClass(dim.status)}`}>{num(dim.score)}</span>
      </div>
      <div className="eval-dim-bar">
        <div
          className={`eval-dim-fill eval-dim-${dim.status}`}
          style={{ width: `${Math.max(0, Math.min(100, dim.score))}%` }}
        />
      </div>
    </div>
  )
}

function SpofRow({ spof }: { spof: SpofEntry }) {
  return (
    <div className="eval-row">
      <span className="chip chip-off">SPOF</span>
      <code>{spof.node_id}</code>
      <span className="small muted">
        {spof.blast_radius} — {spof.reason}
      </span>
    </div>
  )
}

function BottleneckRow({ bn }: { bn: BottleneckEntry }) {
  return (
    <div className="eval-row">
      <span className="chip chip-off">bottleneck</span>
      <code>{bn.node_id}</code>
      <span className="small muted">
        demand {num(bn.demand)} vs capacity {num(bn.capacity)} {bn.unit}
      </span>
    </div>
  )
}

function RequirementRow({ req }: { req: RequirementOutcome }) {
  return (
    <div className="eval-row">
      {statusChip(req.status)}
      <code>{req.requirement_id}</code>
      <span className="small muted">
        {req.reason ?? ''}
        {req.confidence !== 'high' ? ` (${req.confidence} confidence)` : ''}
      </span>
    </div>
  )
}

function RecommendationCard({ rec }: { rec: Recommendation }) {
  return (
    <div className="eval-rec">
      <div className="eval-rec-problem">{rec.problem.replace(/_/g, ' ')}</div>
      <div className="eval-rec-body">
        <strong>{rec.recommendation}</strong>
        <div className="small muted">{rec.expected_benefit}</div>
        {!!rec.tradeoffs?.length && (
          <div className="small muted">Tradeoffs: {rec.tradeoffs.join(' · ')}</div>
        )}
        {!!rec.alternatives?.length && (
          <div className="small muted">Alternatives: {rec.alternatives.join(' · ')}</div>
        )}
        {rec.confidence !== 'high' && <span className="chip">{rec.confidence} confidence</span>}
      </div>
    </div>
  )
}

const GROUP_ORDER: RuleStatus[] = ['FAIL', 'WARNING', 'UNKNOWN', 'INFO']

export function EvaluationPanel({
  result,
  loading,
  error,
  workload,
  onClose,
  onEvaluate,
}: EvaluationPanelProps) {
  const [rpsText, setRpsText] = useState(workload.rps === null ? '' : String(workload.rps))
  const [readText, setReadText] = useState(
    workload.readRatio === null ? '' : String(Math.round(workload.readRatio * 100)),
  )

  useEffect(() => {
    setRpsText(workload.rps === null ? '' : String(workload.rps))
    setReadText(
      workload.readRatio === null ? '' : String(Math.round(workload.readRatio * 100)),
    )
  }, [workload])

  const submit = (): void => {
    const rps = rpsText.trim() === '' ? null : Number(rpsText)
    let readRatio: number | null = null
    if (readText.trim() !== '') {
      readRatio = Number(readText) / 100
      if (readRatio <= 0 || readRatio >= 1) readRatio = null
    }
    onEvaluate({
      rps: rps !== null && Number.isFinite(rps) && rps > 0 ? rps : null,
      readRatio,
    })
  }

  const grouped = new Map<RuleStatus, RuleResult[]>()
  const passed: RuleResult[] = []
  for (const finding of result?.rule_results ?? []) {
    if (finding.status === 'PASS') {
      passed.push(finding)
      continue
    }
    const list = grouped.get(finding.status) ?? []
    list.push(finding)
    grouped.set(finding.status, list)
  }

  return (
    <aside className="eval-panel" aria-label="Evaluation results">
      <div className="eval-panel-head">
        <h3>Evaluation</h3>
        {result && statusChip(result.summary.overall_status)}
        <button type="button" className="btn ghost small-btn" onClick={onClose}>
          Close
        </button>
      </div>

      <div className="eval-workload">
        <label className="field">
          Demand (rps)
          <input
            type="number"
            min={1}
            placeholder="e.g. 5000"
            value={rpsText}
            onChange={(e) => setRpsText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
        </label>
        <label className="field">
          Read ratio (%)
          <input
            type="number"
            min={1}
            max={99}
            placeholder="e.g. 90"
            value={readText}
            onChange={(e) => setReadText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
        </label>
        <button type="button" className="btn primary small-btn" onClick={submit} disabled={loading}>
          {loading ? 'Evaluating…' : result ? 'Re-evaluate' : 'Evaluate'}
        </button>
      </div>

      {error && <div className="eval-error">{error}</div>}

      {!result && !loading && !error && (
        <p className="muted">
          Set a demand model and evaluate. Deterministic checks run first — AI critique is a later
          phase.
        </p>
      )}

      {result && (
        <div className="eval-scroll">
          <section className="eval-section">
            <h4>Dimensions</h4>
            {result.summary.dimension_scores.map((dim) => (
              <DimensionBar key={dim.dimension} dim={dim} />
            ))}
            <p className="small muted">
              demand ≈{' '}
              {result.metrics.demand_rps_estimated === null
                ? 'not set'
                : `${num(result.metrics.demand_rps_estimated)} rps`}{' '}
              · reads {num(result.metrics.read_rps_estimated ?? 0)} / writes{' '}
              {num(result.metrics.write_rps_estimated ?? 0)} ({result.metrics.read_demand_basis})
            </p>
          </section>

          {[...GROUP_ORDER].map((status) => {
            const list = grouped.get(status) ?? []
            if (!list.length) return null
            return (
              <section key={status} className="eval-section">
                <h4>
                  {status.charAt(0) + status.slice(1).toLowerCase()}s ({list.length})
                </h4>
                {list.map((finding) => (
                  <FindingCard key={finding.rule_id} finding={finding} />
                ))}
              </section>
            )
          })}
          {!!passed.length && (
            <p className="small muted">{passed.length} further checks passed.</p>
          )}

          {!!result.spofs.length && (
            <section className="eval-section">
              <h4>Single points of failure ({result.spofs.length})</h4>
              {result.spofs.map((spof) => (
                <SpofRow key={spof.node_id} spof={spof} />
              ))}
            </section>
          )}

          {!!result.bottlenecks.length && (
            <section className="eval-section">
              <h4>Bottlenecks ({result.bottlenecks.length})</h4>
              {result.bottlenecks.map((bn) => (
                <BottleneckRow key={`${bn.node_id}-${bn.unit}`} bn={bn} />
              ))}
            </section>
          )}

          {!!result.requirement_outcomes.length && (
            <section className="eval-section">
              <h4>Requirements ({result.requirement_outcomes.length})</h4>
              {result.requirement_outcomes.map((req) => (
                <RequirementRow key={req.requirement_id} req={req} />
              ))}
            </section>
          )}

          {!!result.recommendations.length && (
            <section className="eval-section">
              <h4>Suggestions ({result.recommendations.length})</h4>
              {result.recommendations.map((rec) => (
                <RecommendationCard key={rec.problem} rec={rec} />
              ))}
            </section>
          )}

          <p className="small muted">
            rule set v{result.rule_version} · deterministic engine, no LLM involved
          </p>
        </div>
      )}
    </aside>
  )
}
