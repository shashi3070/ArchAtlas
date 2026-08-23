import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api/client'
import { useProgress } from '../state/progress'

interface TopicSummary {
  id: string
  title: string
  category: string
  order: number
  summary: string
  prerequisites: string[]
  section_slugs: string[]
  section_titles: string[]
  quiz_count: number
}

export function TopicsPage() {
  const [topics, setTopics] = useState<TopicSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const progress = useProgress()

  useEffect(() => {
    api
      .get<TopicSummary[]>('/api/topics')
      .then(setTopics)
      .catch((e: Error) => setError(e.message))
  }, [])

  const filtered = useMemo(() => {
    if (!topics) return null
    const q = query.trim().toLowerCase()
    if (!q) return topics
    return topics.filter(
      (t) =>
        t.title.toLowerCase().includes(q) ||
        t.summary.toLowerCase().includes(q) ||
        t.category.includes(q),
    )
  }, [topics, query])

  if (error) return <main className="page">Failed to load topics: {error}</main>
  if (!filtered) return <main className="page">Loading topics…</main>

  return (
    <main className="page">
      <header className="page-head">
        <h1>Learning tracks</h1>
        <p className="muted">
          {progress.stats
            ? `${progress.stats.topics_completed} of ${progress.stats.topics_total} completed (${progress.stats.completion_pct}%)`
            : 'Track your progress as you go'}
        </p>
        <input
          type="search"
          placeholder="Filter topics…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="filter topics"
        />
      </header>

      <div className="topic-grid">
        {filtered.map((t) => {
          const done = progress.isTopicCompleted(t.id)
          const prereqs = t.prerequisites.filter((p) => !progress.isTopicCompleted(p))
          return (
            <article key={t.id} className={`card topic-card${done ? ' topic-done' : ''}`}>
              <div className="topic-card-head">
                <h3>
                  <Link to={`/learn/${t.id}`}>{t.title}</Link>
                </h3>
                {done && <span className="chip chip-ok">done</span>}
              </div>
              <p>{t.summary}</p>
              <footer className="topic-meta">
                <span className="chip">{t.category}</span>
                <span>{t.section_slugs.length} sections</span>
                <span>{t.quiz_count} quiz questions</span>
              </footer>
              {prereqs.length > 0 && (
                <p className="muted small">Suggested first: {prereqs.join(', ')}</p>
              )}
            </article>
          )
        })}
      </div>

      {filtered.length === 0 && <p>No topics match “{query}”.</p>}
    </main>
  )
}
