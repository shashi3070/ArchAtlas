# Patterns
- **Virtual nodes**: 100-200 vnodes per physical node gives <5% std-dev in load with 10 nodes.
- **Bounded loads**: cap each node's share at `(1 + epsilon) * average` and spill to the next node on the ring to prevent hotspots.
- **Replication**: own a key on N consecutive nodes for fault tolerance.
- **Jump hashing**: an O(1) alternative when you only need to map key to bucket and node count changes are infrequent.
- **Rendezvous hashing**: highest-random-weight mapping; simpler to reason about but O(N) per lookup.
