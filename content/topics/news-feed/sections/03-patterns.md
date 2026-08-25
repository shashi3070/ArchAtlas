# Patterns
- **Feed ranking**: ML model with features (recency, relationship strength, content type, engagement history).
- **Content deduplication**: same post shared by multiple friends appears once.
- **Real-time streaming**: Kafka + Flink for live feed updates.
- **Feed cache**: Redis sorted sets with post IDs; TTL = 7 days.
- **Media pre-fetching**: preload images/videos for the top 5 posts.
- **A/B testing**: compare ranking algorithms for engagement metrics.
