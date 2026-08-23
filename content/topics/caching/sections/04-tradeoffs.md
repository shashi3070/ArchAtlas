# Tradeoffs
Caching trades freshness and complexity for speed. Longer TTLs raise hit rates and staleness together; shorter ones protect correctness but erode savings. Invalidation is famously hard: event-driven invalidation (subscribe to change feeds) stays fresh but couples cache to write paths; TTL-only decouples fully but accepts staleness windows.

Memory is finite - eviction policy decides who survives pressure. LRU punishes scan patterns (one pass evicts everything); LFU resists scans but clings to formerly hot items. Watch the *hit rate* and *backend load* dashboards, not just latency: a cache can look fast while quietly leaking load to the database.
