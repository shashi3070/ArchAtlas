# Patterns
- **Cache-aside with TTL**: cache short_code→URL mappings; 80% hit rate expected.
- **CDN edge caching**: cache 301 redirects at edge; TTL matches URL expiry.
- **ID generation**: Snowflake ID → Base62 for globally unique, collision-free codes.
- **Bloom filter**: pre-check if a code exists before DB write to avoid collisions.
- **Analytics pipeline**: Kafka → Flink for real-time click aggregation.
- **Custom domains**: map custom short domains via CNAME records; API resolves tenant first.
