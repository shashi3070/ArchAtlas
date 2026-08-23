# Mistakes
- **Caching authenticated API responses by URL alone** - one user's data served to another; vary on auth or skip cache.
- **Query strings busting caches inconsistently** - normalize parameter order or use versioned paths.
- **Purging entire distributions on deploy** - thundering herd on origin; purge selectively or rely on hashed assets.
- **Forgetting `Vary` correctness** - compressed variants and device-specific content colliding in cache.
- **No origin shields** - every PoP miss independently hammers origin during cold starts.
