import { useEffect, useState } from 'react'
import { api } from '../../api/client'

export interface NodeGuide {
  s: string
  w: string
  use: string[]
  avoid: string[]
  after: string[]
  to: string[]
  props: Record<string, string>
  size: Record<string, string>
  world: string[]
  pat: { n: string; d: string }[]
  pits: string[]
  tips: string[]
}

export function NodeGuideModal({
  nodeType,
  onClose,
}: {
  nodeType: string
  onClose: () => void
}) {
  const [guide, setGuide] = useState<NodeGuide | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api
      .get<NodeGuide>(`/api/components/${nodeType}/guide`)
      .then((g) => {
        setGuide(g)
        setLoading(false)
      })
      .catch((e: Error) => {
        setError(e.message)
        setLoading(false)
      })
  }, [nodeType])

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="node-guide-modal" onClick={(e) => e.stopPropagation()}>
        <div className="node-guide-header">
          <h2>{nodeType.replace(/_/g, ' ')}</h2>
          <button type="button" className="btn ghost" onClick={onClose}>
            ×
          </button>
        </div>

        {loading && <p className="muted">Loading guide…</p>}
        {error && <p className="muted error">Error: {error}</p>}

        {guide && (
          <div className="node-guide-body">
            <section className="guide-section">
              <h3>Summary</h3>
              <p>{guide.s}</p>
            </section>

            <section className="guide-section">
              <h3>How It Works</h3>
              <p>{guide.w}</p>
            </section>

            <section className="guide-section">
              <h3>When to Use</h3>
              <ul>
                {guide.use.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </section>

            <section className="guide-section">
              <h3>When to Avoid</h3>
              <ul>
                {guide.avoid.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </section>

            {guide.world.length > 0 && (
              <section className="guide-section">
                <h3>Real-World Examples</h3>
                <ul>
                  {guide.world.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </section>
            )}

            {guide.pat.length > 0 && (
              <section className="guide-section">
                <h3>Patterns</h3>
                {guide.pat.map((p, i) => (
                  <div key={i} className="guide-pattern">
                    <strong>{p.n}</strong>
                    <p>{p.d}</p>
                  </div>
                ))}
              </section>
            )}

            <section className="guide-section">
              <h3>Pitfalls</h3>
              <ul>
                {guide.pits.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </section>

            <section className="guide-section">
              <h3>Interview Tips</h3>
              <ul>
                {guide.tips.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </section>

            {Object.keys(guide.props).length > 0 && (
              <section className="guide-section">
                <h3>Key Properties</h3>
                <dl className="guide-props">
                  {Object.entries(guide.props).map(([key, desc]) => (
                    <div key={key} className="guide-prop-row">
                      <dt>{key}</dt>
                      <dd>{desc}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            )}

            {Object.keys(guide.size).length > 0 && (
              <section className="guide-section">
                <h3>Sizing</h3>
                <dl className="guide-props">
                  {Object.entries(guide.size).map(([key, desc]) => (
                    <div key={key} className="guide-prop-row">
                      <dt>{key}</dt>
                      <dd>{desc}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            )}

            {guide.after.length > 0 && (
              <section className="guide-section">
                <h3>Connects From</h3>
                <div className="guide-tags">
                  {guide.after.map((t) => (
                    <span key={t} className="guide-tag">
                      {t}
                    </span>
                  ))}
                </div>
              </section>
            )}

            {guide.to.length > 0 && (
              <section className="guide-section">
                <h3>Connects To</h3>
                <div className="guide-tags">
                  {guide.to.map((t) => (
                    <span key={t} className="guide-tag">
                      {t}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
