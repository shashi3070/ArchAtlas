import { Link } from 'react-router-dom'

/**
 * Phase 4 placeholder - the challenge engine lands next. The route exists so
 * navigation is complete from day one.
 */
export function ChallengesPage() {
  return (
    <main className="page">
      <header className="page-head">
        <h1>Challenges</h1>
        <p className="muted">Challenge engine arrives in Phase 4.</p>
      </header>
      <div className="card feature-card">
        <h3>Coming next</h3>
        <p>
          Guided builds (URL shortener, notification fan-out, rate-limited API) and repair
          drills where you fix a deliberately broken architecture against the deterministic
          evaluator.
        </p>
        <p>
          Meanwhile you can practice freely in the <Link to="/lab">Lab</Link>.
        </p>
      </div>
    </main>
  )
}
