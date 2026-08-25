# Common Mistakes
- **No idempotency on financial operations**: the most critical use case, often forgotten.
- **Using sequential IDs as idempotency keys**: guessable; client can accidentally reuse.
- **No expiry on idempotency keys**: unbounded storage growth.
- **Race condition on first request**: two simultaneous requests with the same key may both execute.
- **Client generating different keys for retries**: must reuse the exact same key for the logical operation.
