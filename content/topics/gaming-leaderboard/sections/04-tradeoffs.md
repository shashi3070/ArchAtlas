# Tradeoffs
**Redis vs DB**: Redis is O(log N) but memory-limited; DB is durable but slower.
**Global vs regional**: global is simpler; regional is faster for local leaderboards.
**Real-time vs periodic**: real-time is expensive; periodic (every 5 min) is cheaper.

**When to prefer Redis**: high-frequency updates; sub-10ms latency required.
**When to prefer DB**: historical leaderboards; low update frequency.
