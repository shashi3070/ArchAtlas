import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  agentApi,
  type AgentProposal,
  type ApplyReport,
  type ChatMessageInput,
  type ProviderInfo,
  type ProvidersReply,
} from '../../api/agent'
import { useAuth } from '../../state/auth'
import type { CanonicalArchitectureGraph } from '../../graph/toArchitectureGraph'

interface Props {
  graph: () => CanonicalArchitectureGraph
  onApply: (proposal: AgentProposal) => ApplyReport
  onClose: () => void
  /** Storage namespace so lab vs each challenge keep independent histories. */
  scope?: string
}

interface ChatEntry extends ChatMessageInput {
  suggest?: string[]
  fix?: AgentProposal | null
  applied?: boolean
  note?: ApplyReport
}

const QUICK_PROMPTS = [
  'Explain my latest evaluation result',
  'Critique this design',
  'How can I improve it?',
]

const MAX_PERSISTED = 60

function chatStorageKey(scope: string): string {
  return `sdp.chat.${scope}`
}

function loadChat(scope: string): ChatEntry[] {
  try {
    const raw = window.localStorage.getItem(chatStorageKey(scope))
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter(
      (m): m is ChatEntry =>
        !!m &&
        typeof m === 'object' &&
        ((m as ChatEntry).role === 'user' || (m as ChatEntry).role === 'assistant') &&
        typeof (m as ChatEntry).content === 'string',
    )
  } catch {
    return []
  }
}

export function AskPanel({ graph, onApply, onClose, scope = 'lab' }: Props) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [providers, setProviders] = useState<ProvidersReply | null>(null)
  const [providerId, setProviderId] = useState('')
  const [models, setModels] = useState<string[] | null>(null)
  const [modelChoice, setModelChoice] = useState('')
  const [messages, setMessages] = useState<ChatEntry[]>(() => loadChat(scope))
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    try {
      if (messages.length === 0) {
        window.localStorage.removeItem(chatStorageKey(scope))
      } else {
        window.localStorage.setItem(
          chatStorageKey(scope),
          JSON.stringify(messages.slice(-MAX_PERSISTED)),
        )
      }
    } catch {
      /* storage full/blocked */
    }
  }, [messages, scope])

  useEffect(() => {
    agentApi
      .providers()
      .then((p) => {
        setProviders(p)
        const active = p.providers.find((x) => x.id === p.active && (x.key_present || !x.requires_key))
        if (active) setProviderId(active.id)
      })
      .catch(() => setProviders({ active: 'none', providers: [] }))
  }, [])

  useEffect(() => {
    if (!providerId) {
      setModels(null)
      setModelChoice('')
      return
    }
    let cancelled = false
    setModels(null)
    setModelChoice('')
    agentApi
      .models(providerId)
      .then((r) => {
        if (!cancelled) setModels(r.error ? [] : r.models)
      })
      .catch(() => {
        if (!cancelled) setModels([])
      })
    return () => { cancelled = true }
  }, [providerId])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [messages, busy])

  const selected: ProviderInfo | undefined =
    providers?.providers.find((p) => p.id === providerId) ?? undefined
  const keyMissing =
    selected !== undefined && selected.requires_key && !selected.key_present

  const send = async (text: string) => {
    const content = text.trim()
    if (!content || busy) return
    const next: ChatEntry[] = [...messages, { role: 'user', content }]
    setMessages(next)
    setInput('')
    setBusy(true)
    setError(null)
    try {
      const history: ChatMessageInput[] = next.map(({ role, content: c }) => ({
        role,
        content: c,
      }))
      const reply = await agentApi.chat(graph(), history, providerId, '', modelChoice)
      setMessages([
        ...next,
        {
          role: 'assistant',
          content: reply.reply,
          suggest: (reply.suggest ?? []).filter(Boolean).slice(0, 4),
          fix:
            reply.fix &&
            (reply.fix.add_nodes.length > 0 ||
              reply.fix.connect.length > 0 ||
              reply.fix.set_properties.length > 0 ||
              reply.fix.remove_node_ids.length > 0)
              ? reply.fix
              : null,
        },
      ])
    } catch (e) {
      const msg = (e as Error).message || 'Unknown error'
      if (msg.includes('429') || msg.toLowerCase().includes('rate limit')) {
        setError(
          'Rate limit reached. The free tier has limited tokens per minute. Try again in ~50s or switch to a smaller model.',
        )
      } else {
        setError(msg)
      }
    } finally {
      setBusy(false)
    }
  }

  const startNewChat = () => {
    if (busy) return
    setMessages([])
    setError(null)
    setInput('')
  }

  // ── Login gate: show sign-in prompt if not authenticated ──
  if (!user) {
    return (
      <aside className="eval-panel" aria-label="ask the mentor">
        <div className="eval-panel-head">
          <h3>Ask the mentor</h3>
          <button type="button" className="btn ghost small-btn" onClick={onClose}>
            Close
          </button>
        </div>
        <div className="ask-login-gate">
          <div className="ask-login-icon">🔒</div>
          <h4>Sign in required</h4>
          <p>You need to sign in to use the AI mentor chat.</p>
          <button
            type="button"
            className="btn primary"
            onClick={() => navigate('/login')}
          >
            Sign in with Google
          </button>
          <p className="muted small" style={{ marginTop: 12 }}>
            Free tier: 100 AI requests/day &middot; 10s cooldown
          </p>
        </div>
      </aside>
    )
  }

  return (
    <aside className="eval-panel" aria-label="ask the mentor">
      <div className="eval-panel-head">
        <h3>Ask the mentor</h3>
        <button
          type="button"
          className="btn ghost small-btn"
          onClick={startNewChat}
          disabled={busy}
          title="Clear this conversation and start fresh"
        >
          + New chat
        </button>
        <button type="button" className="btn ghost small-btn" onClick={onClose}>
          Close
        </button>
      </div>

      <div className="ask-provider-row">
        <label className="muted small" htmlFor="llm-provider">
          Provider
        </label>
        <select
          id="llm-provider"
          value={providerId}
          onChange={(e) => setProviderId(e.target.value)}
        >
          <option value="" disabled>
            Select provider…
          </option>
          {(providers?.providers ?? []).map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
              {p.active ? ' (default)' : ''}
            </option>
          ))}
        </select>
        {selected &&
          (keyMissing ? (
            <span className="chip chip-off">no API key available</span>
          ) : selected.requires_key ? (
            <span className="chip chip-ok">key configured</span>
          ) : (
            <span className="chip chip-ok">no key needed</span>
          ))}
        {!providers && <span className="chip">loading…</span>}
      </div>

      {selected && !keyMissing && (
        <div className="ask-provider-row">
          <label className="muted small" htmlFor="llm-model">
            Model
          </label>
          <select
            id="llm-model"
            value={modelChoice}
            onChange={(e) => setModelChoice(e.target.value)}
          >
            <option value="">
              {selected.default_model || 'provider default'}
            </option>
            {(models ?? [])
              .filter((m) => m !== selected.default_model)
              .map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
          </select>
          {models === null && <span className="chip">loading models…</span>}
        </div>
      )}

      <div className="ask-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <p className="muted small ask-intro">
            The mentor sees your current canvas and its evaluation. Ask anything, or try:
            <span className="ask-chips">
              {QUICK_PROMPTS.map((q) => (
                <button
                  key={q}
                  type="button"
                  className="btn ghost small-btn"
                  disabled={busy || keyMissing || !selected}
                  onClick={() => void send(q)}
                >
                  {q}
                </button>
              ))}
            </span>
          </p>
        )}
        {messages.map((m, i) =>
          m.role === 'user' ? (
            <div key={i} className="ask-bubble ask-bubble-user">
              {m.content}
            </div>
          ) : (
            <div key={i} className="ask-entry">
              <div className="ask-bubble ask-bubble-mentor">
                <p>{m.content}</p>
                {m.fix && (
                  <div className="ask-fix">
                    {m.fix.summary && <div className="chal-narrative">{m.fix.summary}</div>}
                    <ul className="muted small">
                      {m.fix.add_nodes.map((a, j) => (
                        <li key={`a${j}`}>
                          + {a.name || a.component_type} ({a.component_type}
                          {(a.replicas ?? 1) > 1 ? ` · x${a.replicas}` : ''})
                        </li>
                      ))}
                      {m.fix.connect.map((c, j) => (
                        <li key={`c${j}`}>
                          ↳ connect {c.source_ref} → {c.target_ref} [{c.traffic_type}]
                        </li>
                      ))}
                      {m.fix.set_properties.map((s, j) => (
                        <li key={`s${j}`}>⚙ configure {s.match_component_type}</li>
                      ))}
                      {m.fix.remove_node_ids.map((id, j) => (
                        <li key={`r${j}`}>− remove {id}</li>
                      ))}
                    </ul>
                    {m.applied ? (
                      <>
                        <span className="chip chip-ok">applied to canvas</span>
                        {m.note && m.note.skipped.length > 0 && (
                          <span className="muted small">
                            {m.note.applied} applied · could not resolve:{' '}
                            {m.note.skipped.join('; ')}
                          </span>
                        )}
                      </>
                    ) : (
                      <button
                        type="button"
                        className="btn primary small-btn"
                        onClick={() => {
                          const report = onApply(m.fix!)
                          setMessages((msgs) =>
                            msgs.map((x, k) =>
                              k === i ? { ...x, applied: true, note: report } : x,
                            ),
                          )
                        }}
                      >
                        Apply to canvas
                      </button>
                    )}
                  </div>
                )}
              </div>
              {!busy && i === messages.length - 1 && (m.suggest?.length ?? 0) > 0 && (
                <div className="ask-chips">
                  {m.suggest!.map((s) => (
                    <button
                      key={s}
                      type="button"
                      className="btn ghost small-btn"
                      disabled={busy || keyMissing}
                      onClick={() => void send(s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ),
        )}
        {busy && <div className="ask-bubble ask-bubble-mentor muted">thinking…</div>}
        {error && <div className="eval-error">{error}</div>}
      </div>

      <div className="ask-composer">
        <input
          type="text"
          placeholder={
            keyMissing
              ? `No API key available for ${selected?.label ?? 'this provider'}`
              : 'Ask about your design…'
          }
          disabled={!selected || keyMissing || busy}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !busy && !keyMissing && selected) void send(input)
          }}
        />
        <button
          type="button"
          className="btn primary"
          disabled={!selected || keyMissing || busy || !input.trim()}
          onClick={() => void send(input)}
        >
          Send
        </button>
      </div>
    </aside>
  )
}
