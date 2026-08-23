# How It Works
Read strategies:

- **Cache-aside (lazy)** - app checks cache; on miss, reads store, fills cache, returns. Simplest and most common; first reader pays the cost.
- **Read-through** - the cache library itself fetches from the store on miss; app code never sees the miss.

Write strategies:

- **Write-through** - update cache and store synchronously; reads always consistent, writes slower.
- **Write-behind** - acknowledge at cache, flush to store asynchronously; fast writes risk loss on crash.
- **Invalidate-on-write** - delete the cached copy; next read refills. Avoids stale-writes but causes a thundering read.

Eviction: **LRU** keeps recently used items, **LFU** frequent ones; **TTL** bounds staleness regardless of access patterns. Real systems combine TTL with size-bounded LRU (Redis `allkeys-lru`).
