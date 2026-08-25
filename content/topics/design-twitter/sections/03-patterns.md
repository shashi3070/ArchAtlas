# Patterns
- **Hybrid fan-out**: write-based for regular users; read-based for celebrities.
- **Timeline caching**: Redis sorted sets with tweet IDs; cursor-based pagination.
- **Inverted index**: tokens → tweet IDs for full-text search.
- **Trending detection**: sliding window count + velocity ranking.
- **Graph storage**: follow graph stored in a distributed graph database.
- **Real-time streaming**: Kafka for event processing and analytics.
