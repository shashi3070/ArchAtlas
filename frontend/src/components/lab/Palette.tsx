import { useEffect, useMemo, useState } from 'react'

import { api } from '../../api/client'
import { nodeVisual } from '../../graph/nodeVisuals'
import type { CatalogComponent } from '../../state/labStore'

interface Group {
  label: string
  items: CatalogComponent[]
}

const GROUP_ORDER = [
  'Clients',
  'Traffic',
  'Compute',
  'Cache',
  'Data',
  'Search & Analytics',
  'Messaging',
  'Processing',
  'Identity',
  'Observability',
  'Communication',
  'Coordination',
  'Workflow',
  'Business',
  'Notifications',
  'Media',
  'Realtime',
  'AI',
  'ML',
  'Patterns',
  'Misc',
]

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
  const [query, setQuery] = useState('')

  const groups = useMemo(() => {
    if (!components) return []
    let filtered = components
    if (allowed && allowed.length > 0) {
      filtered = filtered.filter((c) => allowed.includes(c.type))
    }
    const q = query.trim().toLowerCase()
    if (q) {
      const hay = (c: CatalogComponent) =>
        [c.name, c.type, c.category, c.description, ...(c.capabilities ?? []), ...(c.helps_with ?? [])]
          .join(' ')
          .toLowerCase()
      filtered = filtered.filter((c) => hay(c).includes(q))
    }
    return groupComponents(filtered)
  }, [components, allowed, query])

  if (error) return <div className="palette-error">Catalog unavailable: {error}</div>

  return (
    <aside className="palette" aria-label="component palette">
      <div className="palette-title">Components</div>
      <input
        type="search"
        className="palette-search"
        placeholder="Search nodes…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="search components"
      />
      {groups.map((g) => (
        <div key={g.label} className={`palette-group${g.label === 'Patterns' ? ' palette-patterns' : ''}`}>
          <div className="palette-group-label">{g.label}</div>
          {g.items.map((c) => {
            const visual = nodeVisual(c.type)
            const Icon = visual.icon
            return (
              <button
                key={c.type}
                type="button"
                className={`palette-item${c.kind === 'pattern' ? ' palette-item-pattern' : ''}`}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData('application/sdp-component', c.type)
                  e.dataTransfer.effectAllowed = 'copy'
                  onDragStart(c)
                }}
                title={`${c.description}\n\nCapabilities: ${c.capabilities.join(', ')}${
                  c.does_not_solve?.length ? `\nDoes not solve: ${c.does_not_solve.join(', ')}` : ''
                }`}
              >
                <span
                  className="palette-item-icon"
                  style={{ color: c.kind === 'pattern' ? '#475569' : visual.color }}
                >
                  <Icon size={13} strokeWidth={2.2} />
                </span>
                {c.name}
              </button>
            )
          })}
        </div>
      ))}
      {components !== null && groups.length === 0 && (
        <p className="muted small">{query ? 'No matches.' : 'No allowed components.'}</p>
      )}
    </aside>
  )
}
