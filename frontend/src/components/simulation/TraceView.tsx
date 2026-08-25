import { useEffect, useState } from 'react'
import type { TracePath } from '../../api/simulation'

interface Props {
  traces: TracePath[]
  nodeNameMap?: Record<string, string>
}

export function TraceView({ traces, nodeNameMap }: Props) {
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [animStep, setAnimStep] = useState(-1)

  const trace = traces[selectedIdx]
  if (!trace) return <p className="muted">No trace paths available.</p>

  const hopCount = trace.hops.length

  // Animate one hop at a time
  useEffect(() => {
    if (animStep < 0 || animStep >= hopCount) return
    const timer = setTimeout(() => setAnimStep((s) => s + 1), 300)
    return () => clearTimeout(timer)
  }, [animStep, hopCount])

  const nodeName = (id: string) => nodeNameMap?.[id] ?? id

  return (
    <div className="trace-view">
      <div className="trace-header">
        <label className="muted small">
          Trace path
          <select
            value={selectedIdx}
            onChange={(e) => {
              setSelectedIdx(Number(e.target.value))
              setAnimStep(-1)
            }}
            style={{ marginLeft: 8 }}
          >
            {traces.map((t, i) => (
              <option key={i} value={i}>
                {t.path_nodes.map((n) => nodeName(n)).join(' → ')} ({t.total_latency_ms.toFixed(0)}ms)
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="btn ghost small-btn"
          onClick={() => setAnimStep(animStep < 0 ? 0 : hopCount)}
        >
          {animStep >= 0 && animStep < hopCount ? 'Skip ▶▶' : '▶ Animate'}
        </button>
      </div>

      <div className="trace-timeline">
        {trace.hops.map((hop, i) => {
          const visible = animStep < 0 || i <= animStep
          const active = animStep >= 0 && i === animStep
          return (
            <div
              key={`${hop.node_id}-${i}`}
              className={`trace-hop${visible ? ' trace-hop-visible' : ''}${active ? ' trace-hop-active' : ''}`}
            >
              <div className="trace-dot" />
              {i < hopCount - 1 && <div className="trace-line" />}
              <div className="trace-hop-info">
                <span className="trace-hop-name">{nodeName(hop.node_id)}</span>
                <span className="trace-hop-type muted">{hop.node_type}</span>
                <span className="trace-hop-latency">
                  {hop.latency_ms.toFixed(1)}ms
                  {hop.cache_hit && <span className="trace-cache-hit"> cache HIT</span>}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      <div className="trace-summary muted small">
        Total latency: <strong>{trace.total_latency_ms.toFixed(1)} ms</strong> across{' '}
        {hopCount} hops
      </div>
    </div>
  )
}
