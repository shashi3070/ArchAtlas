import { create } from 'zustand'

import type { LabEdge, LabNode } from '../graph/fromArchitectureGraph'

interface Snapshot {
  nodes: LabNode[]
  edges: LabEdge[]
}

export interface CatalogComponent {
  type: string
  category: string
  name: string
  description: string
  capabilities: string[]
  palette?: { group?: string; icon?: string; color?: string }
  capacity_defaults?: Record<string, unknown>
}

interface LabState {
  nodes: LabNode[]
  edges: LabEdge[]
  past: Snapshot[]
  future: Snapshot[]
  selectedNodeId: string | null
  selectedEdgeId: string | null
  archId: string | null
  archName: string
  dirty: boolean

  loadGraph: (nodes: LabNode[], edges: LabEdge[], meta?: { id?: string; name?: string }) => void
  commit: (mutate: (draft: { nodes: LabNode[]; edges: LabEdge[] }) => void) => void
  silentNodesChange: (nodes: LabNode[]) => void
  undo: () => void
  redo: () => void
  selectNode: (id: string | null) => void
  selectEdge: (id: string | null) => void
  setArchId: (id: string | null) => void
  setArchName: (name: string) => void
}

const clone = <T,>(value: T): T =>
  typeof structuredClone === 'function' ? structuredClone(value) : JSON.parse(JSON.stringify(value)) as T

let nodeSeq = 0
export function nextNodeId(componentType: string): string {
  nodeSeq += 1
  return `${componentType}-${nodeSeq}`
}

let edgeSeq = 0
export function nextEdgeId(): string {
  edgeSeq += 1
  return `e-${edgeSeq}`
}

export const useLab = create<LabState>((set) => ({
  nodes: [],
  edges: [],
  past: [],
  future: [],
  selectedNodeId: null,
  selectedEdgeId: null,
  archId: null,
  archName: 'Untitled design',
  dirty: false,

  loadGraph: (nodes, edges, meta) =>
    set((s) => ({
      nodes,
      edges,
      past: [],
      future: [],
      selectedNodeId: null,
      selectedEdgeId: null,
      dirty: true,
      archId: meta?.id ?? s.archId,
      archName: meta?.name ?? s.archName,
    })),

  commit: (mutate) =>
    set((state) => {
      const before = { nodes: state.nodes, edges: state.edges }
      const draft = clone(before)
      mutate(draft)
      return {
        nodes: draft.nodes,
        edges: draft.edges,
        past: [...state.past.slice(-49), clone(before)],
        future: [],
        dirty: true,
      }
    }),

  // Position drags update without flooding history.
  silentNodesChange: (nodes) => set({ nodes }),

  undo: () =>
    set((state) => {
      const prev = state.past[state.past.length - 1]
      if (!prev) return state
      return {
        nodes: prev.nodes,
        edges: prev.edges,
        past: state.past.slice(0, -1),
        future: [{ nodes: state.nodes, edges: state.edges }, ...state.future].slice(0, 50),
        dirty: true,
        selectedNodeId: null,
        selectedEdgeId: null,
      }
    }),

  redo: () =>
    set((state) => {
      const next = state.future[0]
      if (!next) return state
      return {
        nodes: next.nodes,
        edges: next.edges,
        past: [...state.past, { nodes: state.nodes, edges: state.edges }],
        future: state.future.slice(1),
        dirty: true,
      }
    }),

  selectNode: (id) => set({ selectedNodeId: id, selectedEdgeId: null }),
  selectEdge: (id) => set({ selectedEdgeId: id, selectedNodeId: null }),
  setArchId: (id) => set({ archId: id }),
  setArchName: (name) => set({ archName: name }),
}))

export function addNode(component: CatalogComponent, position: { x: number; y: number }): void {
  const id = nextNodeId(component.type)
  useLab.getState().commit(({ nodes }) => {
    nodes.push({
      id,
      type: 'component',
      position,
      data: {
        label: component.name,
        componentType: component.type,
        technology: null,
        capacity: {},
        availability:
          typeof component.capacity_defaults?.default_instances === 'number' &&
          component.capacity_defaults.default_instances > 1
            ? { replicas: component.capacity_defaults.default_instances }
            : { replicas: 1 },
        deployment: {},
        properties: {},
      },
    })
  })
  useLab.getState().selectNode(id)
}
