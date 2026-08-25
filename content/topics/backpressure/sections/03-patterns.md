# Patterns
- **Reactive streams**: `Subscription.request(n)` gives the consumer control over the rate.
- **Bounded channel**: Go channel with capacity N; send blocks when full.
- **Bulkhead**: isolate failure domains so one slow consumer doesn't block others.
- **Circuit breaker + backpressure**: when the circuit opens, the producer stops sending entirely.
- **Load shedding**: drop low-priority messages when the system is overloaded.
- **Adaptive rate limiting**: adjust the producer's rate based on consumer lag or latency metrics.
