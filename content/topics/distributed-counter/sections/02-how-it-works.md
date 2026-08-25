# How It Works
1. User likes a post → increment counter in local region.
2. Counter is sharded: POST_ID % N → increment counter shard.
3. Regional aggregate: sum all shards for regional count.
4. Global merge: periodically sum regional counts for global count.
5. Read: serve approximate count (regional + partial global).

Counter storage: Redis (fast increments) + periodic snapshot to DB (durability).
Sharding: 10-100 shards per counter to distribute write load.
