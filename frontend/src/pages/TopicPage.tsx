import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../api/client'
import { Markdown } from '../lib/markdown'
import { useProgress } from '../state/progress'

interface Section {
  slug: string
  title: string
  order: number
  content_md: string
}

interface QuizItem {
  q: string
  options: string[]
  answer: number
  explain: string
}

interface Topic {
  id: string
  title: string
  category: string
  order: number
  summary: string
  prerequisites: string[]
  related_challenges: string[]
  objectives: string[]
  quiz: QuizItem[]
  sections: Section[]
}

function Quiz({ topicId, items }: { topicId: string; items: QuizItem[] }) {
  const [answers, setAnswers] = useState<(number | null)[]>(() => items.map(() => null))
  const [graded, setGraded] = useState(false)
  const setItem = useProgress((s) => s.setItem)

  const allAnswered = answers.every((a) => a !== null)
  const score = useMemo(
    () => answers.filter((a, i) => a === items[i].answer).length / items.length,
    [answers, items],
  )

  if (items.length === 0) return null

  return (
    <section className="card quiz" aria-label="quiz">
      <h3>Check yourself</h3>
      {items.map((item, qi) => (
        <div key={qi} className="quiz-item">
          <p>
            <strong>{qi + 1}.</strong> {item.q}
          </p>
          <div className="quiz-options">
            {item.options.map((opt, oi) => {
              let cls = 'quiz-option'
              if (graded) {
                if (oi === item.answer) cls += ' correct'
                else if (answers[qi] === oi) cls += ' wrong'
              }
              return (
                <button
                  key={oi}
                  type="button"
                  className={cls}
                  onClick={() => {
                    if (graded) return
                    setAnswers((prev) => prev.map((a, i) => (i === qi ? oi : a)))
                    setGraded(false)
                  }}
                >
                  {opt}
                </button>
              )
            })}
          </div>
          {graded && <p className="muted small">{item.explain}</p>}
        </div>
      ))}
      <div className="quiz-actions">
        {!graded ? (
          <button
            type="button"
            className="btn primary"
            disabled={!allAnswered}
            onClick={() => {
              setGraded(true)
              void setItem(`${topicId}#quiz`, 'topic', true, score)
            }}
          >
            Grade answers
          </button>
        ) : (
          <>
            <span className={score === 1 ? 'chip chip-ok' : 'chip chip-warn'}>
              Score: {Math.round(score * 100)}%
            </span>
            {score < 1 && (
              <button
                type="button"
                className="btn ghost"
                onClick={() => {
                  setAnswers(items.map(() => null))
                  setGraded(false)
                }}
              >
                Retry
              </button>
            )}
          </>
        )}
      </div>
    </section>
  )
}

export function TopicPage() {
  const { topicId } = useParams<{ topicId: string }>()
  const [topic, setTopic] = useState<Topic | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeSlug, setActiveSlug] = useState<string | null>(null)
  const progress = useProgress()
  const refresh = progress.refresh

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    setTopic(null)
    setError(null)
    api
      .get<Topic>(`/api/topics/${topicId}`)
      .then((t) => {
        setTopic(t)
        setActiveSlug(t.sections[0]?.slug ?? null)
      })
      .catch((e: Error) => setError(e.message))
  }, [topicId])

  if (error)
    return (
      <main className="page">
        <p>{error}</p>
        <Link to="/learn">← All topics</Link>
      </main>
    )
  if (!topic || !activeSlug) return <main className="page">Loading…</main>

  const activeSection = topic.sections.find((s) => s.slug === activeSlug)!
  const done = progress.isTopicCompleted(topic.id)

  return (
    <main className="page topic-page">
      <nav className="crumbs">
        <Link to="/learn">Topics</Link> <span>/</span> <span>{topic.title}</span>
      </nav>

      <header className="topic-head">
        <h1>
          {topic.title} {done && <span className="chip chip-ok">completed</span>}
        </h1>
        <p>{topic.summary}</p>
        <ul className="objectives">
          {topic.objectives.map((o) => (
            <li key={o}>{o}</li>
          ))}
        </ul>
      </header>

      <div className="topic-layout">
        <aside className="toc" aria-label="sections">
          <ol>
            {topic.sections.map((s) => (
              <li key={s.slug}>
                <button
                  type="button"
                  className={`toc-link${s.slug === activeSlug ? ' active' : ''}`}
                  onClick={() => setActiveSlug(s.slug)}
                >
                  {s.title}
                  {progress.isSectionCompleted(topic.id, s.slug) && ' ✓'}
                </button>
              </li>
            ))}
          </ol>
          <label className="toc-complete">
            <input
              type="checkbox"
              checked={done}
              onChange={(e) =>
                void progress.setItem(topic.id, 'topic', e.target.checked)
              }
            />
            Mark topic complete
          </label>
        </aside>

        <article className="lesson">
          <Markdown source={activeSection.content_md} />
          <footer className="lesson-nav">
            <button
              type="button"
              className="btn ghost"
              onClick={() => {
                void progress.setItem(
                  `${topic.id}#${activeSlug}`,
                  'section',
                  true,
                )
                const idx = topic.sections.findIndex((s) => s.slug === activeSlug)
                if (idx < topic.sections.length - 1) {
                  setActiveSlug(topic.sections[idx + 1].slug)
                }
              }}
            >
              Mark read & continue →
            </button>
          </footer>

          <Quiz topicId={topic.id} items={topic.quiz} />
        </article>
      </div>
    </main>
  )
}
