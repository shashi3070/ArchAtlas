# Patterns
- **Geohash indexing**: encode lat/long as string; nearby search = prefix match + neighbor cells.
- **PostGIS**: spatial extension for PostgreSQL; supports ST_DWithin, ST_Contains, etc.
- **Two-phase query**: coarse filter (geohash cells) → fine filter (exact distance).
- **Business ranking**: ML model combining distance, rating, reviews, and recency.
- **Cache**: Redis with geohash as key; TTL matches business data freshness.
- **Replication**: read replicas for the business database to handle read traffic.
