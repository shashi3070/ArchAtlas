import { create } from 'zustand'

import { api } from '../api/client'

export interface ProgressEntry {
  item_id: string
  kind: string
  completed: boolean
  quiz_score: number | null
  updated_at: string
}

export interface ProgressStats {
  topics_completed: number
  topics_total: number
  completion_pct: number
}

interface ProgressState {
  entries: Map<string, ProgressEntry>
  stats: ProgressStats | null
  loaded: boolean
  refresh: () => Promise<void>
  setItem: (itemId: string, kind: 'topic' | 'section', completed: boolean, quizScore?: number) => Promise<void>
  isTopicCompleted: (topicId: string) => boolean
  isSectionCompleted: (topicId: string, slug: string) => boolean
}

export const useProgress = create<ProgressState>((set, get) => ({
  entries: new Map(),
  stats: null,
  loaded: false,

  refresh: async () => {
    try {
      const data = await api.get<{ entries: ProgressEntry[]; stats: ProgressStats }>(
        '/api/progress',
      )
      set({
        entries: new Map(data.entries.map((e) => [e.item_id, e])),
        stats: data.stats,
        loaded: true,
      })
    } catch {
      // Progress requires the backend; learning pages stay usable without it.
    }
  },

  setItem: async (itemId, kind, completed, quizScore) => {
    // Optimistic update; server response reconciles.
    const prev = get().entries
    const next = new Map(prev)
    next.set(itemId, {
      item_id: itemId,
      kind,
      completed,
      quiz_score: quizScore ?? prev.get(itemId)?.quiz_score ?? null,
      updated_at: new Date().toISOString(),
    })
    const stats = get().stats
    let nextStats = stats
    if (kind === 'topic' && stats) {
      const wasDone = prev.get(itemId)?.completed ?? false
      if (wasDone !== completed) {
        const topics_completed = Math.max(
          0,
          stats.topics_completed + (completed ? 1 : -1),
        )
        nextStats = {
          ...stats,
          topics_completed,
          completion_pct:
            stats.topics_total > 0
              ? Math.round((1000 * topics_completed) / stats.topics_total) / 10
              : 0,
        }
      }
    }
    set({ entries: next, stats: nextStats })
    try {
      await api.put('/api/progress', { item_id: itemId, kind, completed, quiz_score: quizScore })
    } catch {
      set({ entries: prev, stats })
    }
  },

  isTopicCompleted: (topicId) => get().entries.get(topicId)?.completed ?? false,

  isSectionCompleted: (topicId, slug) =>
    get().entries.get(`${topicId}#${slug}`)?.completed ?? false,
}))
