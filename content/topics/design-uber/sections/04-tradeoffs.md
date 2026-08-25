# Tradeoffs
**Real-time vs batch ETA**: real-time is accurate but expensive; batch is cheaper but stale.
**Eager vs lazy matching**: eager matches immediately; lazy batches for efficiency.
**Geohash vs quadtree**: geohash is simpler; quadtree handles variable density better.

**When to prefer geohash**: moderate density; Redis-backed.
**When to prefer quadtree**: high density variation; need dynamic resizing.
