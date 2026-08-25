# Tradeoffs
**Geohash vs R-tree**: geohash is simpler and works well with Redis; R-tree is more accurate for irregular regions.
**Pre-computed vs on-the-fly**: pre-computed geohash cells are faster; on-the-fly is more accurate.
**PostGIS vs DynamoDB**: PostGIS is feature-rich; DynamoDB is horizontally scalable.

**When to prefer PostGIS**: complex spatial queries; moderate scale.
**When to prefer DynamoDB**: high scale; simple key-value lookups.
