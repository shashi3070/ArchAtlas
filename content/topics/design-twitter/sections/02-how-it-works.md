# How It Works
1. **Post tweet**: user posts → write to their timeline + fan-out to followers' feeds.
2. **Timeline**: fan-out-on-write for regular users; fan-out-on-read for celebrities.
3. **Search**: tweets are indexed in an inverted index (tokens → tweet IDs).
4. **Trending**: count tweet topics in a time window; rank by velocity.
5. **Notifications**: push to followers' devices when a followed account tweets.
6. **Media**: images/videos uploaded to CDN; URLs stored in tweet metadata.

Architecture: Manhattan (distributed KV store), Gizzard (sharding), Lucene (search), Kafka (event streaming).
