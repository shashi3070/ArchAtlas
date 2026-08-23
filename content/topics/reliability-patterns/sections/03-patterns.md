# Patterns
- **Graceful degradation tiers**: personalization off -> recommendations cached-yesterday -> static defaults -> feature hidden.
- **Hedge requests**: send a second copy after p95 delay; cuts tail latency for idempotent reads.
- **Failover & redundancy**: active-active regions, warm standbys, automated promotion tested regularly.
- **Backpressure propagation**: bounded queues reject/delay upstream rather than growing unbounded; callers shed.
- **Chaos drills**: kill pods, inject latency monthly; reliability is rehearsed, not hoped for.
