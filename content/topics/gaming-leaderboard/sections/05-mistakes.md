# Common Mistakes
- **No tiebreaking**: players with the same score have inconsistent ranks.
- **Polling instead of push**: clients polling every second waste resources.
- **No expiry**: inactive players remain on the leaderboard forever.
- **Single Redis instance**: SPOF; use Redis Cluster for high availability.
- **Ignoring score manipulation**: client-side score submissions can be cheated; validate server-side.
