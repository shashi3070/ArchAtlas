# Patterns
- **Event-driven CQRS**: write side publishes events; read side rebuilds projections from events.
- **CQRS + Event Sourcing**: write side stores events as the source of truth; read models are rebuilt from events.
- **Separate databases**: write DB (PostgreSQL) and read DB (Elasticsearch) can be entirely different technologies.
- **Synchronous read model**: for low-latency reads, the read model is updated synchronously (violating pure CQRS but practical).
- **Audit trail**: events provide a complete history of all state changes.
- **Read model variants**: the same events can build multiple read models (e.g., analytics, reporting, UI views).
