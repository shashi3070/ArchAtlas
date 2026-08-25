import { useState } from 'react'
import { useLab } from '../../state/labStore'
import { NodeGuideModal } from './NodeGuideModal'

export function NodeInspector() {
  const nodes = useLab((s) => s.nodes)
  const selectedNodeId = useLab((s) => s.selectedNodeId)
  const commit = useLab((s) => s.commit)
  const [showGuide, setShowGuide] = useState(false)

  const node = nodes.find((n) => n.id === selectedNodeId)
  if (!node) return null

  const availability = (node.data.availability ?? {}) as Record<string, unknown>
  const setAvailability = (key: string, value: unknown) =>
    commit(({ nodes: ns }) => {
      const target = ns.find((n) => n.id === node.id)
      if (target) target.data.availability = { ...(target.data.availability ?? {}), [key]: value }
    })
  const setData = (key: string, value: unknown) =>
    commit(({ nodes: ns }) => {
      const target = ns.find((n) => n.id === node.id)
      if (target) (target.data as Record<string, unknown>)[key] = value
    })

  return (
    <aside className="inspector" aria-label="node properties">
      <h3>{String(node.data.componentType)}</h3>

      <button
        type="button"
        className="btn ghost small-btn"
        onClick={() => setShowGuide(true)}
      >
        Open full guide
      </button>

      <label className="field">
        Name
        <input
          type="text"
          value={String(node.data.label)}
          onChange={(e) => setData('label', e.target.value)}
        />
      </label>

      <label className="field">
        Replicas
        <input
          type="number"
          min={1}
          max={100}
          value={Number(availability.replicas ?? 1)}
          onChange={(e) => setAvailability('replicas', Math.max(1, Number(e.target.value)))}
        />
      </label>

      <label className="check-field">
        <input
          type="checkbox"
          checked={Boolean(availability.multi_az)}
          onChange={(e) => setAvailability('multi_az', e.target.checked)}
        />
        Multi-AZ
      </label>

      <label className="check-field">
        <input
          type="checkbox"
          checked={Boolean(availability.multi_region)}
          onChange={(e) => setAvailability('multi_region', e.target.checked)}
        />
        Multi-region
      </label>

      <button
        type="button"
        className="btn ghost small-btn"
        onClick={() =>
          commit(({ nodes: ns, edges: eds }) => {
            const idx = ns.findIndex((n) => n.id === node.id)
            if (idx >= 0) ns.splice(idx, 1)
            for (let i = eds.length - 1; i >= 0; i--) {
              if (eds[i].source === node.id || eds[i].target === node.id) eds.splice(i, 1)
            }
          })
        }
      >
        Delete node
      </button>

      {showGuide && (
        <NodeGuideModal
          nodeType={String(node.data.componentType)}
          onClose={() => setShowGuide(false)}
        />
      )}
    </aside>
  )
}
