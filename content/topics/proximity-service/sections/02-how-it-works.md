# How It Works
1. User shares location (lat/long) + search query ('restaurants').
2. Service computes geohash for the location.
3. Queries the geospatial index for businesses in nearby cells.
4. Filters by radius and keyword relevance.
5. Ranks results by distance + rating + popularity.
6. Returns top-K results with business details.

Business data: stored in PostgreSQL with PostGIS extension or DynamoDB with geohash as partition key.
Index: geohash-based (Redis sorted sets) or R-tree (PostGIS).
