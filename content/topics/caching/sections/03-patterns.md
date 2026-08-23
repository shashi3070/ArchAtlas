# Patterns
- **Multi-tier**: CDN -> API cache -> object cache -> DB buffer pool. Each tier absorbs misses from the tier above; overall hit rate multiplies.
- **Stampede protection**: coalesce identical in-flight misses (single-flight), lock the refill, or serve stale-while-revalidate so one refresher updates while others read the old value.
- **Negative caching**: cache "not found" briefly - repeated lookups of nonexistent IDs otherwise hammer the store.
- **Cache warming**: pre-populate known-hot keys after deploys or failover so users never see a cold-start cliff.
- **Partitioned cluster**: consistent hashing spreads keys across Redis nodes; hot keys get replicas or local in-process caching on top.
