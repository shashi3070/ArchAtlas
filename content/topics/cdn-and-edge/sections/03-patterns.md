# Patterns
- **Immutable hashed assets + short-TTL HTML**: releases flip HTML pointers instantly; old assets remain valid for returning sessions.
- **Stale-while-revalidate**: serve cached instantly, refresh in background - perceived latency without staleness pain.
- **Edge compute personalization**: cookies parsed at edge, personalized fragments fetched from origin APIs; static shell served from cache.
- **Multi-CDN**: latency/routing-based steering between providers for resilience and cost negotiation.
- **Signed URLs**: expiring tokens gate private media through the cache layer.
