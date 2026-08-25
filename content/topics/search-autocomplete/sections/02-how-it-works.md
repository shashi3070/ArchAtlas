# How It Works
1. Client sends keystroke events to the autocomplete service.
2. Service looks up the prefix in the trie.
3. Returns top-K suggestions ranked by frequency.
4. Trie is periodically rebuilt from a snapshot of query logs.
5. Real-time updates adjust frequency counts in-memory.
6. Cache热门 prefixes (e.g., 'how to', 'what is') in Redis.

Components: trie service (in-memory), query log (Kafka), frequency counter (Redis), cache (Redis), trie builder (batch job).
