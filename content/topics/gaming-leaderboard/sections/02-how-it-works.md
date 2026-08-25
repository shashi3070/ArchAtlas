# How It Works
1. Player achieves a score → game server sends score update to leaderboard service.
2. Service updates Redis sorted set: ZADD leaderboard score player_id.
3. Player queries rank: ZREVRANK leaderboard player_id.
4. Top-K players: ZREVRANGE leaderboard 0 9 WITHSCORES.
5. Friends leaderboard: intersection of player's friend set with leaderboard.
6. Periodic snapshot: export leaderboard to DB for historical analysis.

Components: Redis (sorted set), leaderboard service, WebSocket (live updates), snapshot service.
