# Patterns
- **Feed ranking**: ML model scores posts by relevance (engagement prediction, recency, relationship).
- **Pull vs push**: pull = fan-out-on-read; push = fan-out-on-write.
- **Feed cache**: Redis sorted sets with timestamp scores; expire old posts.
- **Post storage**: separate from feed; feed references post IDs.
- **Real-time updates**: WebSocket or SSE pushes new posts to online users.
- **Pagination**: cursor-based; feed list is truncated at a fixed length (e.g., 800 posts).
