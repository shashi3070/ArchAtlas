import type { ApplyReport, AgentProposal } from '../api/agent'
import { markerForDirection, type LabEdge } from './fromArchitectureGraph'
import { useLab, nextNodeId, nextEdgeId } from '../state/labStore'
import type { CatalogComponent } from '../state/labStore'

/**
 * Applies a proposal-only diff from the AI mentor onto the lab canvas.
 * Node refs resolve in order: added-node ref/label -> exact id -> unique
 * component-type match -> unique id-prefix match ("rabbitmq-2" finds the
 * sole rabbitmq-* node). Unresolvable edits are skipped and reported back
 * instead of failing silently.
 */
export function applyProposalToStore(
  proposal: AgentProposal,
  catalogMap: Map<string, CatalogComponent>,
): ApplyReport {
  const skipped: string[] = []
  let applied = 0
  useLab.getState().commit(({ nodes: ns, edges: eds }) => {
    const refToId = new Map<string, string>()
    const maxX = ns.reduce((m, n) => Math.max(m, n.position.x), 0)
    proposal.add_nodes.forEach((a, i) => {
      const comp = catalogMap.get(a.component_type)
      const id = nextNodeId(a.component_type)
      refToId.set(a.ref.trim().toLowerCase(), id)
      const labelKey = (a.name || '').trim().toLowerCase()
      if (labelKey && !refToId.has(labelKey)) refToId.set(labelKey, id)
      ns.push({
        id,
        type: 'component',
        position: { x: maxX + 140, y: i * 110 },
        data: {
          label: a.name || comp?.name || a.component_type,
          componentType: a.component_type,
          technology: null,
          capacity: {},
          availability: { replicas: Math.max(1, a.replicas ?? 1) },
          deployment: {},
          properties: {},
        },
      })
    })
    applied += proposal.add_nodes.length

    const typeOf = (ref: string) => ref.replace(/-\d+$/, '').trim().toLowerCase()
    const resolve = (ref: string): string | null => {
      const key = ref.trim().toLowerCase()
      if (refToId.has(key)) return refToId.get(key)!
      if (ns.some((n) => n.id === ref)) return ref
      const typed = ns.filter((n) => n.data.componentType === typeOf(ref))
      if (typed.length === 1) return typed[0].id
      const prefixed = ns.filter((n) => n.id.toLowerCase().startsWith(`${typeOf(ref)}-`))
      if (prefixed.length === 1) return prefixed[0].id
      return null
    }

    for (const c of proposal.connect) {
      const s = resolve(c.source_ref)
      const t = resolve(c.target_ref)
      if (!s || !t || s === t) {
        skipped.push(`connect ${c.source_ref} → ${c.target_ref}`)
        continue
      }
      applied += 1
      eds.push({
        id: nextEdgeId(),
        source: s,
        target: t,
        markerEnd: markerForDirection('unidirectional'),
        animated: true,
        data: {
          traffic_type:
            c.traffic_type === 'async_event' ||
            c.traffic_type === 'replication' ||
            c.traffic_type === 'batch'
              ? c.traffic_type
              : 'sync_request',
          direction: 'unidirectional',
          protocol: null,
        },
      } as unknown as LabEdge)
    }

    for (const sp of proposal.set_properties) {
      let hit = false
      for (const n of ns) {
        if (n.data.componentType !== sp.match_component_type) continue
        hit = true
        if (sp.properties && Object.keys(sp.properties).length > 0) {
          n.data.properties = { ...(n.data.properties ?? {}), ...sp.properties }
        }
        if (sp.availability && Object.keys(sp.availability).length > 0) {
          n.data.availability = { ...(n.data.availability ?? {}), ...sp.availability }
        }
      }
      if (hit) applied += 1
      else skipped.push(`configure ${sp.match_component_type}`)
    }

    for (const rid of proposal.remove_node_ids) {
      const idx = ns.findIndex((n) => n.id === rid)
      if (idx < 0) {
        skipped.push(`remove ${rid}`)
        continue
      }
      applied += 1
      ns.splice(idx, 1)
      for (let i = eds.length - 1; i >= 0; i--) {
        if (eds[i].source === rid || eds[i].target === rid) eds.splice(i, 1)
      }
    }
  })
  return { applied, skipped }
}
