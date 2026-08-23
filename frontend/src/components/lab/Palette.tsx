import { useEffect, useMemo, useState } from 'react'

import { api } from '../../api/client'
import type { CatalogComponent } from '../../state/labStore'

interface Group {
  label: string
  items: CatalogComponent[]
}

const GROUP_ORDER = ['Traffic', 'Compute', 'Data', 'Messaging', 'Delivery', 'Clients', 'Misc']

export function useComponentCatalog() {
  const [components, setComponents] = useState<CatalogComponent[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<CatalogComponent[]>('/api/components')
      .then(setComponents)
      .catch((e: Error) => setError(e.message))
  }, [])

  return { components, error }
}

export function groupComponents(components: CatalogComponent[]): Group[] {
  const groups = new Map<string, CatalogComponent[]>()
  for (const c of components) {
    const label = c.palette?.group ?? 'Misc'
    const list = groups.get(label) ?? []
    list.push(c)
    groups.set(label, list)
  }
  return [...groups.entries()]
    .map(([label, items]) => ({
      label,
      items: items.sort((a, b) => a.name.localeCompare(b.name)),
    }))
    .sort(
      (a, b) =>
        (GROUP_ORDER.indexOf(a.label) + 1 || 99) - (GROUP_ORDER.indexOf(b.label) + 1 || 99),
    )
}

export function Palette({
  allowed,
  onDragStart,
}: {
  /** Restrict palette to these component types (challenge mode). Empty = all. */
  allowed?: string[]
  onDragStart: (component: CatalogComponent) => void
}) {
  const { components, error } = useComponentCatalog()

  const groups = useMemo(() => {
    if (!components) return []
    const filtered =
      allowed && allowed.length > 0
        ? components.filter((c) => allowed.includes(c.type))
        : components
    return groupComponents(filtered)
  }, [components, allowed])

  if (error) return <div className="palette-error">Catalog unavailable: {error}</div>

  return (
    <aside className="palette" aria-label="component palette">
      <div className="palette-title">Components</div>
      {groups.map((g) => (
        <div key={g.label} className="palette-group">
          <div className="palette-group-label">{g.label}</div>
          {g.items.map((c) => (
            <button
              key={c.type}
              type="button"
              className="palette-item"
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('application/sdp-component', c.type)
                e.dataTransfer.effectAllowed = 'copy'
                onDragStart(c)
              }}
              title={`${c.description}\n\nCapabilities: ${c.capabilities.join(', ')}`}
            >
              {c.name}
            </button>
          ))}
        </div>
      ))}
      {components !== null && groups.length === 0 && (
        <p className="muted small">No allowed components.</p>
      )}
    </aside>
  )
}
