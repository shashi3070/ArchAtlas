# How It Works
1. Client generates a unique idempotency key (UUID) per logical operation.
2. Client sends the key in the request header: `Idempotency-Key: abc-123`.
3. Server checks if the key exists in its store (Redis or DB).
4. If not, execute the operation, store the key with the result, and respond.
5. If yes, return the stored response without re-executing.
6. Keys expire after 24-48 hours to prevent unbounded storage.

The store must be atomic: check-and-set in a single transaction to prevent race conditions.
