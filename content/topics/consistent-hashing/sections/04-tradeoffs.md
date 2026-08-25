# Tradeoffs
**Pros**: Minimal key redistribution on membership change; no central coordinator; works with heterogeneous nodes via weighted virtual nodes.
**Cons**: Range queries are hard because adjacent keys may land on different nodes; rebalancing is gradual, not instant, causing temporary hotspots during rolling deploys; implementation complexity vs. simple modulo sharding.

**When to prefer modulo sharding**: fixed-size clusters where you can afford full reshuffling on resize.
