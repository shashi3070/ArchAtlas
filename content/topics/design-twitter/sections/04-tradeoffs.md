# Tradeoffs
**Chronological vs ranked**: chronological is transparent; ranked maximizes engagement.
**Fan-out cost vs read latency**: write-based is fast to read but expensive to write.
**Search freshness vs cost**: real-time indexing is expensive; batch indexing is cheaper.

**When to prefer chronological**: small networks; transparency.
**When to prefer ranked**: large networks; engagement optimization.
