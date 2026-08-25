# Patterns
- **Event choreography**: loosely coupled; no SPOF; hard to reason about the full flow when steps are many.
- **Orchestration**: clear flow; single place to manage retries and timeouts; SPOF risk.
- **Semantic lock**: keep a flag on the entity (e.g., `order.status = 'pending'`) to prevent conflicting operations during the saga.
- **Countermeasure: read-your-own-writes**: saga state is visible to the originating user only after confirmation.
- **Timeout**: each step has a deadline; if exceeded, trigger compensation.
- **Idempotent steps**: each step must be safe to retry; use idempotency keys.
