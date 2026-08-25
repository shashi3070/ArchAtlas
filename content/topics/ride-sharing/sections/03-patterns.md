# Patterns
- **Geohash indexing**: 2D coordinates → string prefix; nearby search = prefix match + neighbor cells.
- **Quadtree**: hierarchical spatial partitioning; dynamic resizing based on driver density.
- **ETA pre-computation**: road network graph with edge weights = travel time; Dijkstra or contraction hierarchies.
- **Surge pricing**: real-time demand/supply ratio → price multiplier → balance demand.
- **Trip state machine**: REQUESTED → MATCHED → IN_PROGRESS → COMPLETED.
- **Idempotent location updates**: driver sends batched updates; server deduplicates.
