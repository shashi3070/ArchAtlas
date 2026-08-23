# Patterns
- **Read scaling ladder**: verify indexes -> add read replicas -> cache hot objects -> only then partition.
- **Polyglot persistence**: keep the system of record in Postgres; project search documents into OpenSearch and counters into Redis, fed by CDC events.
- **Outbox pattern**: write domain events into an outbox table inside the same transaction, relay publishes them - atomic business-write + publish.
- **Idempotent upserts**: `INSERT ... ON CONFLICT DO UPDATE` makes retried writes safe, essential once producers can duplicate.
- **Backpressure via queue depth**: when writes outrun the DB, queue and batch them (group commit) rather than admitting unbounded concurrency.
