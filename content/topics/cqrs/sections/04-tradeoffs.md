# Tradeoffs
**Pros**: Independent scaling; optimized storage per access pattern; audit trail via events; simpler domain models.
**Cons**: Eventual consistency complexity; more infrastructure (event bus, multiple DBs); operational overhead; more code.

**When to skip**: simple CRUD with balanced read/write ratios; small teams without operational capacity; prototyping.
**When to apply**: high-scale systems with divergent read/write patterns; need for audit history; complex queries that benefit from denormalization.
