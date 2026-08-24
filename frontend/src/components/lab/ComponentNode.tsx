import { Handle, Position, type NodeProps } from '@xyflow/react'

import type { LabNode } from '../../graph/fromArchitectureGraph'
import { nodeVisual } from '../../graph/nodeVisuals'

export function ComponentNode(props: NodeProps) {
  const data = props.data as unknown as LabNode['data']
  const replicas = (data.availability as Record<string, unknown> | undefined)?.replicas
  const isPattern = data.kind === 'pattern'
  const visual = nodeVisual(data.componentType)
  const Icon = visual.icon

  return (
    <div
      className={`cnode ${props.selected ? 'cnode-selected' : ''} ${isPattern ? 'cnode-pattern' : ''}`}
      style={{ ['--nv' as string]: visual.color }}
    >
      <Handle type="target" position={Position.Top} isConnectable />
      <span className="cnode-icon" aria-hidden>
        <Icon size={15} strokeWidth={2.2} />
      </span>
      <div className="cnode-text">
        <div className="cnode-label">{data.label}</div>
        <div className="cnode-sub">
          {data.componentType}
          {typeof replicas === 'number' ? ` · x${replicas}` : ''}
        </div>
      </div>
      <span className="cnode-badge">{visual.abbr}</span>
      <Handle type="source" position={Position.Bottom} isConnectable />
    </div>
  )
}
