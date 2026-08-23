import { useCallback, useEffect, useState } from 'react'
import {
  Background,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type Edge as FlowEdge,
  type EdgeChange,
  type Node as FlowNode,
  type NodeChange,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { toArchitectureGraph } from './graph/toArchitectureGraph'

const initialNodes: FlowNode[] = [
  {
    id: 'client-1',
    position: { x: 40, y: 140 },
    data: { label: 'Web Client', componentType: 'client' },
  },
  {
    id: 'api-1',
    position: { x: 360, y: 140 },
    data: { label: 'API Service', componentType: 'api' },
  },
]

const initialEdges: FlowEdge[] = [
  {
    id: 'e-client-api',
    source: 'client-1',
    target: 'api-1',
    animated: true,
    data: { traffic_type: 'sync_request', protocol: 'https' },
  },
]

export default function App() {
  return (
    <ReactFlowProvider>
      <Lab />
    </ReactFlowProvider>
  )
}

function Lab() {
  const [nodes, setNodes] = useState<FlowNode[]>(initialNodes)
  const [edges, setEdges] = useState<FlowEdge[]>(initialEdges)
  const [exportedJson, setExportedJson] = useState<string | null>(null)
  const [componentCount, setComponentCount] = useState<number | null>(null)

  useEffect(() => {
    fetch('/api/components')
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(String(res.status)))))
      .then((items: unknown[]) => setComponentCount(items.length))
      .catch(() => setComponentCount(null))
  }, [])

  const onNodesChange = useCallback(
    (changes: NodeChange<FlowNode>[]) =>
      setNodes((nds) => applyNodeChanges(changes, nds)),
    [],
  )

  const onEdgesChange = useCallback(
    (changes: EdgeChange<FlowEdge>[]) =>
      setEdges((eds) => applyEdgeChanges(changes, eds)),
    [],
  )

  const onConnect = useCallback(
    (connection: Connection) =>
      setEdges((eds) =>
        addEdge({ ...connection, data: { traffic_type: 'sync_request' } }, eds),
      ),
    [],
  )

  const onExport = () => {
    // The canvas is a view; the export produces the canonical graph contract.
    const graph = toArchitectureGraph({
      id: `smoke-${Date.now()}`,
      version: 1,
      nodes,
      edges,
      metadata: { source: 'phase0-smoke' },
    })
    setExportedJson(JSON.stringify(graph, null, 2))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header className="topbar">
        <strong>System Design Platform</strong>
        <span className="muted">Phase 0 smoke lab</span>
        <span className={`chip ${componentCount === null ? 'chip-off' : ''}`}>
          {componentCount === null
            ? 'API offline'
            : `${componentCount} components loaded`}
        </span>
        <button type="button" onClick={onExport}>
          Export canonical JSON
        </button>
      </header>

      <main style={{ position: 'relative', flex: 1 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>

        {exportedJson !== null && (
          <aside className="json-panel" aria-label="canonical graph json">
            <div className="json-panel-head">
              <span>ArchitectureGraph</span>
              <button type="button" onClick={() => setExportedJson(null)}>
                close
              </button>
            </div>
            <pre>{exportedJson}</pre>
          </aside>
        )}
      </main>
    </div>
  )
}
