import { Handle, Position, type NodeProps } from '@xyflow/react'

import type { LabNode } from '../../graph/fromArchitectureGraph'

const ABBR: Record<string, string> = {
  client: 'CL',
  load_balancer: 'LB',
  api: 'API',
  worker: 'WRK',
  redis: 'RD',
  postgresql: 'PG',
  mongodb: 'MG',
  kafka: 'KF',
  rabbitmq: 'RM',
  cdn: 'CDN',
  object_storage: 'OS',
}

export function ComponentNode(props: NodeProps) {
  const data = props.data as unknown as LabNode['data']
  const replicas = (data.availability as Record<string, unknown> | undefined)?.replicas
  const abbr = ABBR[data.componentType] ?? data.componentType.slice(0, 3).toUpperCase()

  return (
    <div className={`cnode ${props.selected ? 'cnode-selected' : ''}`}>
      <Handle type="target" position={Position.Top} isConnectable />
      <span className="cnode-badge">{abbr}</span>
      <div className="cnode-text">
        <div className="cnode-label">{data.label}</div>
        <div className="cnode-sub">
          {data.componentType}
          {typeof replicas === 'number' ? ` · x${replicas}` : ''}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} isConnectable />
    </div>
  )
}
