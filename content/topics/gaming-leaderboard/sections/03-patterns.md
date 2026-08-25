# Patterns
- **Sorted set**: score = member score; rank is derived from position.
- **Tiebreaking**: encode timestamp in fractional score (score + timestamp/1e12).
- **Sharded leaderboard**: partition by game or region; merge for global rankings.
- **Incremental updates**: ZINCRBY for atomic score increments.
- **Friend leaderboard**: ZINTERSTORE to compute friend-only rankings.
- **Live updates**: WebSocket pushes rank changes to connected players.
