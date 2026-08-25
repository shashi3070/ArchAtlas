# Patterns
- **Fallback on open**: return cached data, default values, or a degraded response.
- **Bulkhead isolation**: combine with thread pool or semaphore isolation to prevent one failing dependency from consuming all threads.
- **Slow-call detection**: trips on latency (e.g., p99 > 5s) not just errors.
- **Per-dependency circuits**: separate circuit for each downstream service; one failure doesn't affect others.
- **Event emitter**: log circuit state changes for observability and alerting.
- **Manual override**: operator can force-open or force-close for emergency situations.
