# Common Mistakes
- **No health checks**: dead instances remain in the pool, causing 502/503 errors.
- **Stale DNS cache**: client caches a downed instance for minutes.
- **Registering before ready**: instance receives traffic before it can serve.
- **Deregistering too early**: instance deregisters during a rolling deploy before the new instance is ready.
- **Single discovery server**: SPOF; use a replicated cluster with at least 3 nodes.
