import { Link } from 'react-router-dom'

const FEATURES = [
  {
    title: 'Learn the pillars',
    body: 'Ten concise topic tracks - from HTTP fundamentals to rate limiting - each with patterns, trade-offs and classic mistakes.',
    to: '/learn',
    cta: 'Browse topics',
  },
  {
    title: 'Build in the Lab',
    body: 'Drag real components onto an infinite canvas. The graph you draw is a strict, validated ArchitectureGraph document.',
    to: '/lab',
    cta: 'Open canvas',
  },
  {
    title: 'Get graded, not vibes',
    body: 'A deterministic evaluator scores your architecture against 50+ rules and maps it to requirement outcomes before any AI comments.',
    to: '/challenges',
    cta: 'Try challenges',
  },
]

export function HomePage() {
  return (
    <main>
      <section className="hero">
        <h1>
          Learn system design by <em>building</em> systems
        </h1>
        <p className="hero-sub">
          Draw architectures on a canvas. Get instant, rule-based feedback grounded in evidence.
          Repair broken designs. Then let the AI tutor explain what changed and why.
        </p>
        <div className="hero-actions">
          <Link className="btn primary" to="/learn">
            Start learning
          </Link>
          <Link className="btn ghost" to="/lab">
            Jump into the Lab
          </Link>
        </div>
      </section>

      <section className="features">
        {FEATURES.map((f) => (
          <article key={f.title} className="card feature-card">
            <h3>{f.title}</h3>
            <p>{f.body}</p>
            <Link to={f.to}>{f.cta} →</Link>
          </article>
        ))}
      </section>

      <section className="card how-it-works">
        <h3>How grading works</h3>
        <ol>
          <li>Your canvas exports a canonical <code>ArchitectureGraph</code> - JSON schemas are the source of truth.</li>
          <li>A deterministic engine runs 46+ rules: SPOF detection, capacity vs demand, cache placement, availability math.</li>
          <li>You see every finding with evidence and a suggested fix. AI explanations come after, citing those findings.</li>
        </ol>
      </section>
    </main>
  )
}
