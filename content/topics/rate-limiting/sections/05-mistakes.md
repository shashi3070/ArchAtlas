# Mistakes
- **Limiting only authenticated paths** - login and signup endpoints are prime brute-force targets.
- **Global lock contention** - one Redis key for the whole API serializes everything; shard by key.
- **In-memory-only counters per instance** - N instances = N times the intended quota; share or aggregate.
- **No client feedback** - silent throttling triggers blind retries worsening the storm.
- **Static thresholds forever** - capacity grows, traffic mixes change; review limits quarterly with data.
