# How It Works
1. Hash every node identifier onto the ring using a uniform hash function.
2. Hash each data key the same way; walk clockwise to find the owning node.
3. When a node departs, its keys slide to the next clockwise neighbour.
4. Virtual nodes multiply each physical node's presence on the ring, improving balance.

The ring can be implemented as a sorted array of `(hash, node)` pairs with binary search for O(log N) lookup, or as a skip list for O(log N) insert/delete.
