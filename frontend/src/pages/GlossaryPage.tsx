import { useEffect, useState } from 'react'

import { api } from '../api/client'

interface Term {
  term: string
  definition: string
}

export function GlossaryPage() {
  const [terms, setTerms] = useState<Term[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<Term[]>('/api/glossary')
      .then(setTerms)
      .catch((e: Error) => setError(e.message))
  }, [])

  if (error) return <main className="page">Failed to load glossary: {error}</main>
  if (!terms) return <main className="page">Loading…</main>

  return (
    <main className="page">
      <header className="page-head">
        <h1>Glossary</h1>
        <p className="muted">{terms.length} terms used across lessons and evaluations.</p>
      </header>
      <dl className="glossary">
        {terms.map((t) => (
          <div key={t.term} className="glossary-item card">
            <dt>{t.term}</dt>
            <dd>{t.definition}</dd>
          </div>
        ))}
      </dl>
    </main>
  )
}
