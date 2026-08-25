# Common Mistakes
- **Too many services too early**: distributed monolith with all the downsides and none of the upsides.
- **Shared databases**: tight coupling defeats the purpose of microservices.
- **Synchronous chains**: deep request chains (A calls B calls C) amplify latency and failure probability.
- **Ignoring observability**: without distributed tracing, debugging becomes impossible.
- **No API versioning**: breaking changes cascade to all consumers.
