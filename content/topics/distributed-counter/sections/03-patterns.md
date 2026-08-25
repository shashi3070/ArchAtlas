# Patterns
- **Counter sharding**: split one logical counter into N physical counters; sum for total.
- **Local aggregation**: batch increments in memory; flush periodically.
- **G-counters (CRDT)**: grow-only counters; merge by taking max per replica.
- **Delta encoding**: store deltas instead of absolute values; reduce storage.
- **In-memory buffering**: buffer increments in memory; flush to Redis/DB every N seconds.
- **Read-your-writes**: after a user likes a post, immediately show the incremented count.
