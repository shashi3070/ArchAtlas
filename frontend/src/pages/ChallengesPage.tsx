import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { challengesApi, type ChallengeSummary } from '../api/challenges'

const FAMILY_TITLES: Record<string, string> = {
  'url-shortener': 'URL Shortener',
  'media-gallery': 'Media Gallery',
  'order-processing': 'Order Processing',
}

const MODE_LABEL: Record<ChallengeSummary['mode'], string> = {
  challenge: 'Build',
  repair: 'Repair drill',
  explore: 'Explore',
  interview: 'Interview',
}

function DifficultyChip({ level }: { level: ChallengeSummary['difficulty'] }) {
  return <span className={`chip diff-${level}`}>{level}</span>
}

export function ChallengesPage() {
  const [items, setItems] = useState<ChallengeSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    challengesApi
      .list()
      .then(setItems)
      .catch((e: Error) => setError(e.message))
  }, [])

  const families = new Map<string, ChallengeSummary[]>()
  const drills: ChallengeSummary[] = []
  for (const c of items ?? []) {
    if (c.chain?.family_id) {
      const list = families.get(c.chain.family_id) ?? []
      list.push(c)
      families.set(c.chain.family_id, list)
    } else {
      drills.push(c)
    }
  }

  return (
    <main className="page">
      <header className="page-head">
        <h1>Challenges</h1>
        <p className="muted">
          Guided builds and repair drills graded by the deterministic evaluator. Pass requires
          score &ge; 70 with no must-have requirement violated.
        </p>
      </header>

      {error && <div className="eval-error">Failed to load challenges: {error}</div>}
      {!items && !error && <p className="muted">Loading…</p>}

      {[...families.entries()].map(([family, list]) => (
        <section key={family} className="challenge-family">
          <h2>{FAMILY_TITLES[family] ?? family}</h2>
          <div className="challenge-grid">
            {list.map((c) => (
              <Link key={c.id} to={`/challenges/${c.id}`} className="challenge-card">
                <div className="challenge-card-head">
                  <span className="chip">Level {c.chain?.level}</span>
                  <DifficultyChip level={c.difficulty} />
                </div>
                <h3>{c.title}</h3>
                {c.narrative && <p className="muted small clamp-2">{c.narrative}</p>}
                <div className="challenge-card-foot muted small">
                  {c.requirement_count} requirements · {c.hint_count} hints
                  {c.has_starting_graph ? '' : ' · start from scratch'}
                </div>
              </Link>
            ))}
          </div>
        </section>
      ))}

      {drills.length > 0 && (
        <section className="challenge-family">
          <h2>Repair drills</h2>
          <p className="muted small">
            A broken architecture is loaded on the canvas — find it and fix it before submitting.
          </p>
          <div className="challenge-grid">
            {drills.map((c) => (
              <Link key={c.id} to={`/challenges/${c.id}`} className="challenge-card">
                <div className="challenge-card-head">
                  <span className="chip chip-warn">{MODE_LABEL[c.mode]}</span>
                  <DifficultyChip level={c.difficulty} />
                </div>
                <h3>{c.title}</h3>
                {c.narrative && <p className="muted small clamp-2">{c.narrative}</p>}
                <div className="challenge-card-foot muted small">
                  {c.requirement_count} requirements · {c.hint_count} hints
                  {c.has_starting_graph ? ' · broken design preloaded' : ''}
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {items !== null && items.length === 0 && !error && (
        <p className="muted">No challenge packs found.</p>
      )}
    </main>
  )
}
