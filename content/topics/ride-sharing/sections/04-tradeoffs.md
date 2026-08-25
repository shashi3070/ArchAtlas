# Tradeoffs
**Geohash vs quadtree**: geohash is simpler and works well with Redis; quadtree handles variable density better.
**Real-time vs batch ETA**: real-time is accurate but expensive; batch is cheaper but stale.
**Eager vs lazy matching**: eager (match immediately on request) vs lazy (batch-match periodically for efficiency).

**When to prefer geohash**: moderate density; Redis-backed; simple implementation.
**When to prefer quadtree**: high density variation (city vs rural); need dynamic resizing.
