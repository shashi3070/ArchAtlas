# Tradeoffs
**Pros**: Complete audit trail; temporal queries; multiple read models; easy debugging (replay events); natural fit for DDD.
**Cons**: Eventual consistency; query complexity; schema evolution challenges; storage grows indefinitely; learning curve.

**When to skip**: simple CRUD; no audit requirements; small team without event sourcing experience.
**When to apply**: financial systems (audit trail); complex domains with many projections; debugging production issues.
