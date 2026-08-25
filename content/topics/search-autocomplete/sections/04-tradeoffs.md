# Tradeoffs
**In-memory vs distributed**: in-memory trie is fastest but limited to one machine; distributed trie (e.g., Redis cluster) scales but adds latency.
**Freshness vs cost**: real-time updates are expensive; batch rebuilds are cheaper but stale.
**Global vs personalized**: global is simpler; personalized requires per-user state.

**When to prefer global**: public search engines; privacy-sensitive applications.
**When to prefer personalized**: e-commerce; content platforms with user accounts.
