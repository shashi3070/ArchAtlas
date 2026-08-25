# Tradeoffs
**Pros**: Safe retries; reduced client complexity; protection against network instability.
**Cons**: Storage overhead for idempotency keys; complexity in distributed systems where keys must be consistent across services; window sizing (too short = vulnerable to late retries; too long = storage bloat).

**When to skip idempotency**: read-only operations (naturally idempotent); fire-and-forget analytics where duplicates are acceptable.
