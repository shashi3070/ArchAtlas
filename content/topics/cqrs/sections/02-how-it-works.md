# How It Works
1. **Command side**: receives input (POST/PUT/DELETE), validates, writes to the write DB, and publishes an event.
2. **Event bus**: carries the event (Kafka, RabbitMQ, or in-process).
3. **Query side**: subscribes to events, updates the read DB (denormalized, query-optimized).
4. **Client reads**: query the read DB directly for fast, pre-computed views.

The read DB can be Elasticsearch for full-text search, Redis for fast key-value lookups, or a separate PostgreSQL with materialized views.
