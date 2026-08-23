import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Background,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  useReactFlow,
  type Connection,
  type Edge as FlowEdge,
  type EdgeChange,
  type NodeChange,
} from '@xyflow/react'

import {
  challengesApi,
  type ChallengeDetail,
  type HintLadder,
  type ScoredSubmission,
  type SubmissionSummary,
} from '../api/challenges'
import { ComponentNode } from '../components/lab/ComponentNode'
import { EdgeInspector } from '../components/lab/EdgeInspector'
import { NodeInspector } from '../components/lab/NodeInspector'
import { Palette, useComponentCatalog } from '../components/lab/Palette'
import {
  fromArchitectureGraph,
  type LabEdge,
  type LabNode,
} from '../graph/fromArchitectureGraph'
import { toArchitectureGraph } from '../graph/toArchitectureGraph'
import { addNode, nextEdgeId, useLab, type CatalogComponent } from '../state/labStore'

const nodeTypes = { component: ComponentNode }

const draftKey = (cid: string) => `sdp.challenge.${cid}.draft`

function statusChipClass(status: string): string {
  switch (status) {
    case 'satisfied':
      return 'chip chip-ok'
    case 'at_risk':
      return 'chip chip-warn'
    case 'violated':
      return 'chip chip-off'
    default:
      return 'chip'
  }
}

function RunChallenge({ cid }: { cid: string }) {
  const store = useLab()
  const { nodes, edges, past, future } = store
  const { screenToFlowPosition } = useReactFlow()
  const [detail, setDetail] = useState<ChallengeDetail | null>(null)
  const [pageError, setPageError] = useState<string | null>(null)
  const [result, setResult] = useState<ScoredSubmission | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [history, setHistory] = useState<SubmissionSummary[]>([])
  const [hintLadder, setHintLadder] = useState<HintLadder | null>(null)
  const [panel, setPanel] = useState<'brief' | 'result'>('brief')
  const dragComponent = useRef<CatalogComponent | null>(null)
  const readyRef = useRef(false)

  const { components } = useComponentCatalog()
  const catalogMap = useRef(new Map<string, CatalogComponent>())
  for (const c of components ?? []) catalogMap.current.set(c.type, c)

  // Snapshot the Lab's state on mount and restore it on unmount, so challenge
  // work lives in the shared canvas store without leaking into free practice.
  useEffect(() => {
    const prev = useLab.getState()
    useLab.setState({
      nodes: [],
      edges: [],
      past: [],
      future: [],
      selectedNodeId: null,
      selectedEdgeId: null,
    })
    let cancelled = false
    challengesApi
      .get(cid)
      .then((ch) => {
        if (cancelled) return
        setDetail(ch)
        let restored = false
        const draftRaw = localStorage.getItem(draftKey(cid))
        if (draftRaw) {
          try {
            const draft = JSON.parse(draftRaw) as { nodes: LabNode[]; edges: LabEdge[] }
            if (Array.isArray(draft.nodes) && draft.nodes.length > 0) {
              useLab.getState().loadGraph(draft.nodes, draft.edges, { name: ch.title })
              restored = true
            }
          } catch {
            /* corrupt draft - fall through to the starting graph */
          }
        }
        if (!restored && ch.starting_graph) {
          const view = fromArchitectureGraph(ch.starting_graph)
          useLab.getState().loadGraph(view.nodes, view.edges, { name: ch.title })
        }
        readyRef.current = true
      })
      .catch((e: Error) => setPageError(e.message))
    return () => {
      cancelled = true
      readyRef.current = false
      useLab.setState({
        nodes: prev.nodes,
        edges: prev.edges,
        past: prev.past,
        future: prev.future,
        archId: prev.archId,
        archName: prev.archName,
        trafficModel: prev.trafficModel,
        selectedNodeId: null,
        selectedEdgeId: null,
      })
    }
  }, [cid])

  // Autosave the working graph so refreshes don't lose progress.
  useEffect(() => {
    if (!readyRef.current) return
    localStorage.setItem(draftKey(cid), JSON.stringify({ nodes, edges }))
  }, [cid, nodes, edges])

  useEffect(() => {
    if (cid) challengesApi.submissions(cid).then(setHistory).catch(() => setHistory([]))
  }, [cid])

  const onNodesChange = useCallback(
    (changes: NodeChange<LabNode>[]) =>
      store.silentNodesChange(applyNodeChanges(changes, store.nodes)),
    [store],
  )

  const onEdgesChange = useCallback(
    (changes: EdgeChange<LabEdge>[]) => {
      if (changes.every((c) => c.type === 'select')) {
        useLab.setState({ edges: applyEdgeChanges(changes, store.edges) })
        return
      }
      store.commit((draft) => {
        draft.edges = applyEdgeChanges(changes, draft.edges)
      })
    },
    [store],
  )

  const onConnect = useCallback(
    (connection: Connection) =>
      store.commit(({ edges: eds }) => {
        addEdge(
          {
            ...connection,
            id: nextEdgeId(),
            data: { traffic_type: 'sync_request', direction: 'unidirectional', protocol: null },
          },
          eds as unknown as FlowEdge[],
        )
      }),
    [store],
  )

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      const componentType = event.dataTransfer.getData('application/sdp-component')
      const component =
        catalogMap.current.get(componentType) ??
        (dragComponent.current?.type === componentType ? dragComponent.current : null)
      if (!component) return
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY })
      addNode(component, position)
    },
    [screenToFlowPosition],
  )

  const onSubmit = async () => {
    setSubmitting(true)
    setPageError(null)
    try {
      const graph = toArchitectureGraph({
        id: `challenge-${cid}`,
        version: 1,
        nodes,
        edges,
        metadata: { source: 'challenge' },
        trafficModel: {},
      })
      const res = await challengesApi.submit(cid, graph)
      setResult(res)
      setPanel('result')
      challengesApi.submissions(cid).then(setHistory).catch(() => {})
    } catch (e) {
      setPageError((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  const revealNextHint = async () => {
    try {
      const next = (hintLadder?.level ?? 0) + 1
      setHintLadder(await challengesApi.hints(cid, next))
    } catch (e) {
      setPageError((e as Error).message)
    }
  }

  if (pageError && !detail) {
    return (
      <main className="page">
        <p className="eval-error">Failed to load challenge: {pageError}</p>
        <Link to="/challenges" className="btn ghost">
          Back to challenges
        </Link>
      </main>
    )
  }

  const revealed = hintLadder?.hints ?? []

  return (
    <div className="lab-shell">
      <div className="lab-toolbar">
        <Link to="/challenges" className="btn ghost" aria-label="back to challenges">
          ← Challenges
        </Link>
        <strong>{detail?.title ?? cid}</strong>
        {detail && (
          <>
            <span className={`chip diff-${detail.difficulty}`}>{detail.difficulty}</span>
            {detail.mode === 'repair' && <span className="chip chip-warn">repair drill</span>}
          </>
        )}
        <span className="toolbar-sep" />
        <button
          type="button"
          className="btn ghost"
          disabled={past.length === 0}
          onClick={store.undo}
        >
          ↶ Undo
        </button>
        <button
          type="button"
          className="btn ghost"
          disabled={future.length === 0}
          onClick={store.redo}
        >
          ↷ Redo
        </button>
        <span className={`chip ${nodes.length === 0 ? 'chip-off' : ''}`}>
          {nodes.length} nodes{detail?.constraints?.find((c) => c.key === 'max_nodes')
            ? ` / ${String(detail.constraints.find((c) => c.key === 'max_nodes')?.value)}`
            : ''}
        </span>
        <span className="toolbar-sep" />
        <button
          type="button"
          className={`btn ${panel === 'brief' ? 'primary' : 'ghost'}`}
          onClick={() => setPanel('brief')}
        >
          Brief
        </button>
        <button
          type="button"
          className={`btn ${panel === 'result' ? 'primary' : 'ghost'}`}
          disabled={!result}
          onClick={() => setPanel('result')}
        >
          Result
        </button>
        <button
          type="button"
          className="btn primary"
          disabled={nodes.length === 0 || submitting}
          onClick={() => void onSubmit()}
        >
          {submitting ? 'Grading…' : 'Submit'}
        </button>
        {result && (
          <span className={`chip ${result.passed ? 'chip-ok' : 'chip-off'}`}>
            Attempt {result.attempt}: {Math.round(result.score)}%
          </span>
        )}
      </div>

      <div className="lab-body">
        <Palette
          allowed={detail?.allowed_components}
          onDragStart={(c) => {
            dragComponent.current = c
          }}
        />

        <div className="lab-canvas">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={(e) => {
              e.preventDefault()
              e.dataTransfer.dropEffect = 'copy'
            }}
            onNodeClick={(_, node) => store.selectNode(node.id)}
            onPaneClick={() => {
              store.selectNode(null)
              store.selectEdge(null)
            }}
            onEdgeClick={(_, edge) => store.selectEdge(edge.id)}
            onNodeDragStop={() => {
              useLab.setState((s) => ({
                past: [...s.past.slice(-49), { nodes: s.nodes, edges: s.edges }],
                future: [],
                dirty: true,
              }))
            }}
            fitView
          >
            <Background />
            <Controls />
          </ReactFlow>

          {store.selectedNodeId && <NodeInspector />}
          {!store.selectedNodeId && store.selectedEdgeId && <EdgeInspector />}

          {panel === 'brief' && detail && (
            <aside className="chal-panel" aria-label="challenge brief">
              <div className="eval-panel-head">
                <h3>Brief</h3>
              </div>
              <div className="eval-scroll">
                {detail.mode === 'repair' && (
                  <p className="chal-note">
                    A broken architecture is already on the canvas. Find the failure modes and fix
                    them before submitting.
                  </p>
                )}
                {detail.narrative && <p className="chal-narrative">{detail.narrative}</p>}

                <h4>Requirements</h4>
                <ul className="req-list">
                  {detail.requirements.map((r) => (
                    <li key={r.id} className="req-item">
                      <span className={`chip prio-${r.priority ?? 'must'}`}>
                        {r.priority ?? 'must'}
                      </span>
                      <div>
                        <div>{r.description}</div>
                        {typeof r.value === 'number' && (
                          <div className="muted small">
                            target: {r.value}
                            {r.unit ? ` ${r.unit}` : ''} ({r.metric})
                          </div>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>

                {(detail.constraints?.length ?? 0) > 0 && (
                  <>
                    <h4>Constraints</h4>
                    <ul className="muted small">
                      {detail.constraints!.map((c) => (
                        <li key={c.key}>
                          {c.key.replace(/_/g, ' ')}: {String(c.value)}
                        </li>
                      ))}
                    </ul>
                  </>
                )}

                <h4>
                  Hints{' '}
                  <span className="muted small">
                    {revealed.length}/{detail.hint_count} revealed
                  </span>
                </h4>
                {revealed.length < detail.hint_count && (
                  <button type="button" className="btn ghost small-btn" onClick={() => void revealNextHint()}>
                    Reveal hint {revealed.length + 1}
                  </button>
                )}
                <ol className="hint-list">
                  {revealed.map((h, i) => (
                    <li key={i}>{h}</li>
                  ))}
                </ol>

                {pageError && <p className="eval-error">{pageError}</p>}
              </div>
            </aside>
          )}

          {panel === 'result' && result && (
            <aside className="chal-panel" aria-label="submission result">
              <div className="eval-panel-head">
                <h3>
                  Result · attempt {result.attempt} · {Math.round(result.score)}%
                </h3>
              </div>
              <div className="eval-scroll">
                <div className={`chal-verdict ${result.passed ? 'pass' : 'fail'}`}>
                  {result.passed
                    ? 'Passed - all gates clear.'
                    : result.blocking_failure
                      ? 'Not passed - the evaluator found a blocking failure.'
                      : `Not passed - score below 70% or a must-have requirement is violated.`}
                </div>

                {result.constraint_violations.length > 0 && (
                  <>
                    <h4>Constraint violations</h4>
                    <ul className="chal-violations">
                      {result.constraint_violations.map((v, i) => (
                        <li key={i}>{v}</li>
                      ))}
                    </ul>
                  </>
                )}

                <h4>Requirement breakdown</h4>
                {result.breakdown.map((b) => (
                  <div key={b.requirement_id} className="eval-row">
                    <span className={`chip prio-${b.priority}`}>{b.priority}</span>
                    <span className={statusChipClass(b.status)}>{b.status}</span>
                    <span className="eval-rule-id">{b.requirement_id}</span>
                    <span className="muted small">
                      {b.points}/{b.weight} pts
                    </span>
                    {b.reason && <div className="eval-message">{b.reason}</div>}
                  </div>
                ))}

                {result.findings.length > 0 && (
                  <>
                    <h4>Evaluator findings</h4>
                    {result.findings.slice(0, 12).map((f, i) => (
                      <div
                        key={i}
                        className={`eval-finding ${
                          f.severity === 'fail'
                            ? 'eval-finding-fail'
                            : f.severity === 'warning'
                              ? 'eval-finding-warning'
                              : ''
                        }`}
                      >
                        <span className="eval-rule-id">{f.rule_id}</span>
                        <p className="eval-message">{f.message}</p>
                      </div>
                    ))}
                  </>
                )}

                {history.length > 0 && (
                  <>
                    <h4>Attempts</h4>
                    <div className="eval-row muted small">
                      {history.map((h) => (
                        <span key={h.attempt} className={`chip ${h.passed ? 'chip-ok' : ''}`}>
                          #{h.attempt}: {Math.round(h.score)}%
                        </span>
                      ))}
                    </div>
                  </>
                )}

                {pageError && <p className="eval-error">{pageError}</p>}
              </div>
            </aside>
          )}
        </div>
      </div>
    </div>
  )
}

export function ChallengeRunPage() {
  const { cid } = useParams<{ cid: string }>()
  if (!cid) {
    return (
      <main className="page">
        <p className="muted">No challenge selected.</p>
        <Link to="/challenges" className="btn ghost">
          Back to challenges
        </Link>
      </main>
    )
  }
  return (
    <ReactFlowProvider>
      <RunChallenge cid={cid} />
    </ReactFlowProvider>
  )
}
