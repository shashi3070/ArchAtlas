import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Background,
  Controls,
  MiniMap,
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

import { architecturesApi } from '../api/architectures'
import { EdgeInspector } from '../components/lab/EdgeInspector'
import { NodeInspector } from '../components/lab/NodeInspector'
import { Palette, useComponentCatalog } from '../components/lab/Palette'
import {
  fromArchitectureGraph,
  type LabEdge,
  type LabNode,
} from '../graph/fromArchitectureGraph'
import { autoLayout } from '../graph/layout'
import { toArchitectureGraph, type CanonicalArchitectureGraph } from '../graph/toArchitectureGraph'
import { addNode, nextEdgeId, useLab, type CatalogComponent } from '../state/labStore'

interface SaveState {
  kind: 'idle' | 'saving' | 'saved' | 'error'
  message?: string
}

function Lab() {
  const store = useLab()
  const { nodes, edges, past, future } = store
  const wrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition } = useReactFlow()
  const [saveState, setSaveState] = useState<SaveState>({ kind: 'idle' })
  const [showLibrary, setShowLibrary] = useState(false)
  const [showVersions, setShowVersions] = useState(false)
  const dragComponent = useRef<CatalogComponent | null>(null)

  const { components } = useComponentCatalog()
  const catalogMap = useMemo(() => {
    const map = new Map<string, CatalogComponent>()
    for (const c of components ?? []) map.set(c.type, c)
    return map
  }, [components])

  // Autosave draft locally so refreshes don't lose work.
  useEffect(() => {
    if (nodes.length === 0) return
    localStorage.setItem(
      'sdp.lab.draft',
      JSON.stringify({ nodes, edges: store.edges, name: store.archName }),
    )
  }, [nodes, store.edges, store.archName])

  const onNodesChange = useCallback(
    (changes: NodeChange<LabNode>[]) =>
      store.silentNodesChange(applyNodeChanges(changes, store.nodes)),
    [store],
  )

  const onEdgesChange = useCallback(
    (changes: EdgeChange<LabEdge>[]) => {
      // Selection changes are silent; deletions go through history.
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
        catalogMap.get(componentType) ??
        (dragComponent.current?.type === componentType ? dragComponent.current : null)
      if (!component) return
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY })
      addNode(component, position)
    },
    [catalogMap, screenToFlowPosition],
  )

  const currentGraph = (): CanonicalArchitectureGraph =>
    toArchitectureGraph({
      id: store.archId ?? `lab-${Date.now()}`,
      version: 1,
      nodes,
      edges,
      metadata: { source: 'lab' },
    })

  const onSave = async () => {
    setSaveState({ kind: 'saving' })
    try {
      if (store.archId) {
        await architecturesApi.update(store.archId, currentGraph())
      } else {
        const meta = await architecturesApi.create(store.archName || 'Untitled design', currentGraph())
        store.setArchId(meta.id)
      }
      setSaveState({ kind: 'saved' })
      setTimeout(() => setSaveState({ kind: 'idle' }), 2000)
    } catch (e) {
      setSaveState({ kind: 'error', message: (e as Error).message })
    }
  }

  const onAutoLayout = () =>
    store.commit((draft) => {
      draft.nodes = autoLayout(draft.nodes, draft.edges.map((e) => ({ source: e.source, target: e.target })))
    })

  const onExportFile = () => {
    const blob = new Blob([JSON.stringify(currentGraph(), null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${store.archName.replace(/\s+/g, '-').toLowerCase()}.architecture.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const onImportFile = async (file: File) => {
    try {
      const text = await file.text()
      const graph = JSON.parse(text) as Parameters<typeof fromArchitectureGraph>[0]
      const view = fromArchitectureGraph(graph)
      store.loadGraph(view.nodes, view.edges, {
        name: file.name.replace(/\.(architecture)?json$/, ''),
      })
      store.setArchName(file.name.replace(/\.(architecture)?json$/, ''))
    } catch (e) {
      alert(`Import failed: ${(e as Error).message}`)
    }
  }

  return (
    <div className="lab-shell">
      <div className="lab-toolbar">
        <input
          className="arch-name"
          value={store.archName}
          onChange={(e) => store.setArchName(e.target.value)}
          aria-label="architecture name"
        />
        <button type="button" className="btn ghost" disabled={past.length === 0} onClick={store.undo}>
          ↶ Undo
        </button>
        <button type="button" className="btn ghost" disabled={future.length === 0} onClick={store.redo}>
          ↷ Redo
        </button>
        <button type="button" className="btn ghost" onClick={onAutoLayout}>
          Auto-layout
        </button>
        <span className="toolbar-sep" />
        <button type="button" className="btn primary" onClick={() => void onSave()}>
          Save
        </button>
        <button type="button" className="btn ghost" onClick={() => setShowLibrary(true)}>
          Open…
        </button>
        <button type="button" className="btn ghost" onClick={() => setShowVersions(true)}>
          Versions
        </button>
        <label className="btn ghost file-btn">
          Import
          <input
            type="file"
            accept=".json,application/json"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) void onImportFile(f)
              e.target.value = ''
            }}
          />
        </label>
        <button type="button" className="btn ghost" onClick={onExportFile}>
          Export
        </button>
        {saveState.kind !== 'idle' && (
          <span
            className={`chip ${
              saveState.kind === 'error' ? 'chip-off' : saveState.kind === 'saved' ? 'chip-ok' : ''
            }`}
          >
            {saveState.kind === 'saving' && 'Saving…'}
            {saveState.kind === 'saved' && 'Saved'}
            {saveState.kind === 'error' && `Error: ${saveState.message}`}
          </span>
        )}
        <span className={`chip ${nodes.length === 0 ? 'chip-off' : ''}`}>
          {nodes.length} nodes · {edges.length} connections
        </span>
      </div>

      <div className="lab-body">
        <Palette
          allowed={undefined}
          onDragStart={(c) => {
            dragComponent.current = c
          }}
        />

        <div className="lab-canvas" ref={wrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
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
              // Commit final positions into history once per drag.
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
            <MiniMap pannable />
          </ReactFlow>

          {showLibrary && (
            <SavedArchitecturesDialog onClose={() => setShowLibrary(false)} />
          )}
          {showVersions && (
            <VersionsDialog archId={store.archId} onClose={() => setShowVersions(false)} />
          )}

          {store.selectedNodeId && <NodeInspector />}
          {!store.selectedNodeId && store.selectedEdgeId && <EdgeInspector />}
        </div>
      </div>
    </div>
  )
}

function SavedArchitecturesDialog({ onClose }: { onClose: () => void }) {
  const [items, setItems] = useState<Awaited<ReturnType<typeof architecturesApi.list>> | null>(null)
  const loadGraph = useLab((s) => s.loadGraph)

  useEffect(() => {
    architecturesApi
      .list()
      .then(setItems)
      .catch(() => setItems([]))
  }, [])

  return (
    <dialog open className="lab-dialog">
      <h3>Saved architectures</h3>
      {(items ?? []).length === 0 && <p className="muted">Nothing saved yet.</p>}
      <ul className="lib-list">
        {(items ?? []).map((a) => (
          <li key={a.id}>
            <button
              type="button"
              className="btn ghost"
              onClick={async () => {
                const full = await architecturesApi.get(a.id)
                const view = fromArchitectureGraph(full.graph)
                loadGraph(view.nodes, view.edges, { id: a.id, name: a.name })
                onClose()
              }}
            >
              {a.name} <span className="muted">v{a.current_version}</span>
            </button>
          </li>
        ))}
      </ul>
      <button type="button" className="btn ghost" onClick={onClose}>
        Close
      </button>
    </dialog>
  )
}

function VersionsDialog({ archId, onClose }: { archId: string | null; onClose: () => void }) {
  const [versions, setVersions] = useState<Awaited<ReturnType<typeof architecturesApi.versions>> | null>(
    null,
  )
  const loadGraph = useLab((s) => s.loadGraph)

  useEffect(() => {
    if (!archId) return
    architecturesApi.versions(archId).then(setVersions).catch(() => setVersions([]))
  }, [archId])

  if (!archId)
    return (
      <dialog open className="lab-dialog">
        <p className="muted">Save this architecture first to track versions.</p>
        <button type="button" className="btn ghost" onClick={onClose}>
          Close
        </button>
      </dialog>
    )

  return (
    <dialog open className="lab-dialog">
      <h3>Version history</h3>
      <ul className="lib-list">
        {(versions ?? []).map((v) => (
          <li key={v.version} className="version-row">
            <span>
              v{v.version} {v.is_current && <span className="chip chip-ok">current</span>}
              <span className="muted small"> {v.note}</span>
            </span>
            <span className="version-actions">
              <button
                type="button"
                className="btn ghost"
                onClick={async () => {
                  const vg = await architecturesApi.versionGraph(archId, v.version)
                  const view = fromArchitectureGraph(vg.graph)
                  loadGraph(view.nodes, view.edges, { id: archId })
                  onClose()
                }}
              >
                View
              </button>
              {!(v.is_current) && (
                <button
                  type="button"
                  className="btn ghost"
                  onClick={async () => {
                    await architecturesApi.restore(archId, v.version)
                    const full = await architecturesApi.get(archId)
                    const view = fromArchitectureGraph(full.graph)
                    loadGraph(view.nodes, view.edges, { id: archId, name: full.name })
                    onClose()
                  }}
                >
                  Restore
                </button>
              )}
            </span>
          </li>
        ))}
      </ul>
      <button type="button" className="btn ghost" onClick={onClose}>
        Close
      </button>
    </dialog>
  )
}

export function LabPage() {
  return (
    <ReactFlowProvider>
      <Lab />
    </ReactFlowProvider>
  )
}
