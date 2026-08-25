# Patterns
- **Idempotency key store**: Redis with TTL for fast lookups; DB table for durable storage.
- **Optimistic approach**: use unique constraints (e.g., `idempotency_id` column) to reject duplicates at the DB level.
- **Event deduplication**: message queues (Kafka) deduplicate by message key within a window.
- **Natural idempotency**: `PUT /users/{id}` with the same body is naturally idempotent.
- **Retry with backoff**: client retries with the same idempotency key on timeout; server returns cached response.
- **Partial execution**: if the operation fails midway, store the partial result and return 500; on retry, the server knows it tried and can resume or return the error.
