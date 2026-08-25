import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api } from '../api/client'

/* ── Types ────────────────────────────────────────────────────── */

interface TranscriptEntry {
  phase: string
  role: 'interviewer' | 'candidate'
  content: string
  timestamp: string
}

interface InterviewSession {
  session_id: string
  scenario: string
  current_phase: string
  transcript: TranscriptEntry[]
  started_at: string
  ended_at: string
}

interface InterviewReport {
  dimension_scores: Record<string, number>
  dimension_evidence: Record<string, string>
  dimension_feedback: Record<string, string>
  overall_recommendation: string
  strengths: string[]
  improvements: string[]
  study_plan: string[]
}

/* ── Phase labels ────────────────────────────────────────────── */

const PHASE_LABELS: Record<string, string> = {
  requirements: 'Requirements',
  scale: 'Scale Estimation',
  api_design: 'API Design',
  data_model: 'Data Model',
  architecture: 'Architecture',
  bottlenecks: 'Bottlenecks',
  scaling: 'Scaling',
  consistency: 'Consistency',
  availability: 'Availability',
  failure_handling: 'Failure Handling',
  observability: 'Observability',
  trade_offs: 'Trade-offs',
  completed: 'Completed',
}

const PHASES_ORDER = [
  'requirements',
  'scale',
  'api_design',
  'data_model',
  'architecture',
  'bottlenecks',
  'scaling',
  'consistency',
  'availability',
  'failure_handling',
  'observability',
  'trade_offs',
]

const PRESET_SCENARIOS = [
  'Design a URL shortener like bit.ly',
  'Design a real-time chat system like WhatsApp',
  'Design a news feed like Twitter/X',
  'Design a video streaming platform like YouTube',
  'Design a ride-sharing service like Uber',
  'Design a distributed payment system',
  'Design a web crawler',
  'Design a notification system',
  'Design a search autocomplete system',
  'Design a gaming leaderboard',
]

/* ── Main component ──────────────────────────────────────────── */

export function InterviewPage() {
  const navigate = useNavigate()

  const [sessionId, setSessionId] = useState<string | null>(null)
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [report, setReport] = useState<InterviewReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [scenario, setScenario] = useState('')
  const [customScenario, setCustomScenario] = useState('')
  const [candidateInput, setCandidateInput] = useState('')

  const [showReport, setShowReport] = useState(false)
  const transcriptEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [session?.transcript])

  /* ── Start interview ─────────────────────────────────────────── */

  const startInterview = useCallback(async () => {
    const selectedScenario = customScenario.trim() || scenario
    if (!selectedScenario) {
      setError('Please select or enter a scenario')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const id = `interview-${Date.now()}`
      const result = await api.post<{
        session_id: string
        phase: string
        message: string
        transcript: TranscriptEntry[]
      }>('/api/interview/start', {
        session_id: id,
        scenario: selectedScenario,
      })
      setSessionId(id)
      setSession({
        session_id: id,
        scenario: selectedScenario,
        current_phase: result.phase,
        transcript: result.transcript,
        started_at: new Date().toISOString(),
        ended_at: '',
      })
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start interview')
    } finally {
      setLoading(false)
    }
  }, [scenario, customScenario])

  /* ── Send candidate message ──────────────────────────────────── */

  const sendMessage = useCallback(async () => {
    if (!sessionId || !candidateInput.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.post<{
        session_id: string
        phase: string
        message: string
        transcript: TranscriptEntry[]
      }>(`/api/interview/${sessionId}/message`, {
        message: candidateInput.trim(),
      })
      setSession((prev) =>
        prev
          ? {
              ...prev,
              current_phase: result.phase,
              transcript: result.transcript,
            }
          : prev,
      )
      setCandidateInput('')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to send message')
    } finally {
      setLoading(false)
    }
  }, [sessionId, candidateInput])

  /* ── Advance to next phase ───────────────────────────────────── */

  const advancePhase = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.post<{
        session_id: string
        phase: string
        message: string
        transcript: TranscriptEntry[]
      }>(`/api/interview/${sessionId}/advance`, {})
      setSession((prev) =>
        prev
          ? {
              ...prev,
              current_phase: result.phase,
              transcript: result.transcript,
            }
          : prev,
      )
      if (result.phase === 'completed') {
        const reportResult = await api.post<{
          session_id: string
          report: InterviewReport
          transcript: TranscriptEntry[]
        }>(`/api/interview/${sessionId}/report`, {})
        setReport(reportResult.report)
        setShowReport(true)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to advance phase')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  /* ── Generate report manually ────────────────────────────────── */

  const generateReport = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.post<{
        session_id: string
        report: InterviewReport
        transcript: TranscriptEntry[]
      }>(`/api/interview/${sessionId}/report`, {})
      setReport(result.report)
      setShowReport(true)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  /* ── Phase progress indicator ────────────────────────────────── */

  const currentPhaseIdx = PHASES_ORDER.indexOf(session?.current_phase ?? '')

  const PhaseProgress = () => (
    <div className="phase-progress">
      {PHASES_ORDER.map((phase, idx) => (
        <div
          key={phase}
          className={`phase-step ${idx < currentPhaseIdx ? 'completed' : idx === currentPhaseIdx ? 'active' : ''}`}
          title={PHASE_LABELS[phase]}
        >
          <span className="phase-step-num">{idx + 1}</span>
          <span className="phase-step-label">{PHASE_LABELS[phase]}</span>
        </div>
      ))}
    </div>
  )

  /* ── Transcript panel ────────────────────────────────────────── */

  const TranscriptPanel = () => (
    <div className="interview-transcript">
      {session?.transcript.map((entry, idx) => (
        <div key={idx} className={`transcript-entry transcript-${entry.role}`}>
          <div className="transcript-meta">
            <span className="transcript-role">
              {entry.role === 'interviewer' ? 'Interviewer' : 'Candidate'}
            </span>
            <span className="transcript-phase">
              {PHASE_LABELS[entry.phase] ?? entry.phase}
            </span>
          </div>
          <div className="transcript-content">{entry.content}</div>
        </div>
      ))}
      <div ref={transcriptEndRef} />
    </div>
  )

  /* ── Report view ─────────────────────────────────────────────── */

  const ReportView = () => {
    if (!report) return null
    return (
      <div className="interview-report">
        <h2>Interview Report</h2>
        <div className="report-recommendation">
          <strong>Recommendation:</strong>{' '}
          <span className={`rec-${report.overall_recommendation}`}>
            {report.overall_recommendation.replace(/_/g, ' ')}
          </span>
        </div>

        <div className="report-scores">
          <h3>Dimension Scores</h3>
          {Object.entries(report.dimension_scores).map(([dim, score]) => (
            <div key={dim} className="score-row">
              <span className="score-dim">{dim.replace(/_/g, ' ')}</span>
              <span className="score-bar">
                <span className="score-fill" style={{ width: `${(score / 5) * 100}%` }} />
              </span>
              <span className="score-value">{score}/5</span>
            </div>
          ))}
        </div>

        <div className="report-section">
          <h3>Strengths</h3>
          <ul>
            {report.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>

        <div className="report-section">
          <h3>Areas for Improvement</h3>
          <ul>
            {report.improvements.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>

        <div className="report-section">
          <h3>Study Plan</h3>
          <ul>
            {report.study_plan.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>

        <button type="button" className="btn" onClick={() => navigate('/challenges')}>
          Back to Challenges
        </button>
      </div>
    )
  }

  /* ── Setup view ──────────────────────────────────────────────── */

  if (!session) {
    return (
      <div className="interview-page">
        <div className="interview-setup">
          <h1>System Design Interview</h1>
          <p className="muted">
            Practice a structured 45-minute system design interview with an AI interviewer.
          </p>

          <div className="setup-scenarios">
            <h3>Select a Scenario</h3>
            <div className="scenario-grid">
              {PRESET_SCENARIOS.map((s) => (
                <button
                  key={s}
                  type="button"
                  className={`scenario-btn${scenario === s ? ' selected' : ''}`}
                  onClick={() => {
                    setScenario(s)
                    setCustomScenario('')
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="setup-custom">
            <h3>Or Enter Custom Scenario</h3>
            <input
              type="text"
              placeholder="e.g., Design a distributed caching system"
              value={customScenario}
              onChange={(e) => {
                setCustomScenario(e.target.value)
                setScenario('')
              }}
              className="custom-scenario-input"
            />
          </div>

          {error && <div className="error-msg">{error}</div>}

          <button
            type="button"
            className="btn primary-btn"
            onClick={startInterview}
            disabled={loading || (!scenario && !customScenario.trim())}
          >
            {loading ? 'Starting...' : 'Start Interview'}
          </button>
        </div>
      </div>
    )
  }

  /* ── Report view (after completion) ──────────────────────────── */

  if (showReport && report) {
    return (
      <div className="interview-page">
        <ReportView />
      </div>
    )
  }

  /* ── Active interview view ───────────────────────────────────── */

  return (
    <div className="interview-page interview-active">
      <div className="interview-header">
        <h2>Interview: {session.scenario}</h2>
        <div className="interview-actions">
          <button type="button" className="btn ghost" onClick={generateReport} disabled={loading}>
            Get Report
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => {
              setSession(null)
              setSessionId(null)
              setReport(null)
              setShowReport(false)
            }}
          >
            New Interview
          </button>
        </div>
      </div>

      <PhaseProgress />

      {error && <div className="error-msg">{error}</div>}

      <div className="interview-layout">
        <div className="interview-canvas-area">
          <div className="canvas-placeholder">
            <p className="muted">
              Canvas area — draw your architecture here. The interviewer can see your design and will
              ask follow-ups based on it.
            </p>
          </div>
        </div>

        <div className="interview-chat-area">
          <TranscriptPanel />

          <div className="interview-input-bar">
            <textarea
              placeholder="Type your answer..."
              value={candidateInput}
              onChange={(e) => setCandidateInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              disabled={loading}
              rows={3}
            />
            <div className="interview-input-actions">
              <button
                type="button"
                className="btn"
                onClick={sendMessage}
                disabled={loading || !candidateInput.trim()}
              >
                Send
              </button>
              <button type="button" className="btn ghost" onClick={advancePhase} disabled={loading}>
                Next Phase →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
