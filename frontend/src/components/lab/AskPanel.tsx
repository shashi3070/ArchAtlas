import { useState } from 'react'

import {
  agentApi,
  type AgentProposal,
  type AgentReply,
  type ProposalReply,
} from '../../api/agent'
import type { CanonicalArchitectureGraph } from '../../graph/toArchitectureGraph'
import type { EvaluationResult } from '../../api/evaluate'

type Tab = 'explain' | 'critique' | 'improve'

interface Props {
  /** Runs a fresh deterministic evaluation (also refreshes the eval panel). */
  onExplain: () => Promise<EvaluationResult>
  graph: () => CanonicalArchitectureGraph
  onApply: (proposal: AgentProposal) => void
  onClose: () => void
}

function ReplyView({ reply }: { reply: AgentReply | null }) {
  if (!reply) return null
  return (
    <div className="ask-reply">
      {reply.source === 'deterministic' && (
        <span className="chip">deterministic summary</span>
      )}
      {reply.cache_hit && <span className="chip chip-ok">cached</span>}
      <p>{reply.text}</p>
    </div>
  )
}

export function AskPanel({ onExplain, graph, onApply, onClose }: Props) {
  const [tab, setTab] = useState<Tab>('explain')
  const [reply, setReply] = useState<AgentReply | null>(null)
  const [proposal, setProposal] = useState<ProposalReply | null>(null)
  const [goal, setGoal] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async (task: Tab) => {
    setBusy(true)
    setError(null)
    try {
      if (task === 'explain') {
        const result = await onExplain()
        setTab('explain')
        setProposal(null)
        setReply(await agentApi.explain(result))
      } else if (task === 'critique') {
        setProposal(null)
        setReply(await agentApi.critique(graph()))
      } else {
        setReply(null)
        setProposal(await agentApi.proposal(graph(), goal))
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <aside className="eval-panel" aria-label="ask the mentor">
      <div className="eval-panel-head">
        <h3>Ask the mentor</h3>
        <button type="button" className="btn ghost small-btn" onClick={onClose}>
          Close
        </button>
      </div>

      <div className="ask-tabs" role="tablist">
        {(['explain', 'critique', 'improve'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            className={`btn ${tab === t ? 'primary' : 'ghost'} ask-tab`}
            onClick={() => setTab(t)}
          >
            {t === 'explain' ? 'Explain result' : t === 'critique' ? 'Critique design' : 'Improve'}
          </button>
        ))}
      </div>

      {tab === 'improve' && (
        <div className="ask-goal">
          <input
            type="text"
            placeholder="Goal (optional), e.g. survive a DB node loss"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
          />
          <button type="button" className="btn primary" disabled={busy} onClick={() => void run('improve')}>
            Propose
          </button>
        </div>
      )}
      {tab !== 'improve' && (
        <div className="ask-runrow">
          <button
            type="button"
            className="btn primary"
            disabled={busy}
            onClick={() => void run(tab)}
          >
            {busy ? 'Thinking…' : tab === 'explain' ? 'Explain' : 'Critique'}
          </button>
          <span className="muted small">
            {tab === 'explain'
              ? 'Grounded in your latest evaluation.'
              : 'Engine findings are attached; the model cannot contradict them.'}
          </span>
        </div>
      )}

      {error && <div className="eval-error">{error}</div>}

      <div className="eval-scroll">
        <ReplyView reply={reply} />

        {proposal && (
          <div className="ask-proposal">
            <h4>Proposed changes</h4>
            <p className="chal-narrative">{proposal.proposal.summary}</p>
            {proposal.proposal.add_nodes.length > 0 && (
              <>
                <h4>Add</h4>
                <ul className="muted small">
                  {proposal.proposal.add_nodes.map((a, i) => (
                    <li key={i}>
                      {a.name || a.component_type} ({a.component_type}
                      {(a.replicas ?? 1) > 1 ? ` · x${a.replicas}` : ''})
                    </li>
                  ))}
                </ul>
              </>
            )}
            {proposal.proposal.connect.length > 0 && (
              <>
                <h4>Connect</h4>
                <ul className="muted small">
                  {proposal.proposal.connect.map((c, i) => (
                    <li key={i}>
                      {c.source_ref} → {c.target_ref} [{c.traffic_type ?? 'sync_request'}]
                    </li>
                  ))}
                </ul>
              </>
            )}
            {proposal.proposal.set_properties.length > 0 && (
              <>
                <h4>Configure</h4>
                <ul className="muted small">
                  {proposal.proposal.set_properties.map((s, i) => (
                    <li key={i}>{s.match_component_type}</li>
                  ))}
                </ul>
              </>
            )}
            {proposal.proposal.remove_node_ids.length > 0 && (
              <>
                <h4>Remove</h4>
                <ul className="muted small">
                  {proposal.proposal.remove_node_ids.map((id, i) => (
                    <li key={i}>{id}</li>
                  ))}
                </ul>
              </>
            )}
            <button
              type="button"
              className="btn primary"
              onClick={() => onApply(proposal.proposal)}
            >
              Apply to canvas
            </button>
            <p className="muted small">
              Nothing is applied without this button - proposals are advisory only.
            </p>
          </div>
        )}
      </div>
    </aside>
  )
}
