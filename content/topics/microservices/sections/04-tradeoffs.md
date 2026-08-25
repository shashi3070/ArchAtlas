# Tradeoffs
**Pros**: Independent deployment; language diversity; targeted scaling; fault isolation; team autonomy.
**Cons**: Network latency between services; distributed transactions; operational complexity (CI/CD, monitoring, tracing); data consistency challenges; testing complexity.

**When to start with a monolith**: small teams, early product-market fit stage, unclear domain boundaries.
**When to split**: team size >20, deployment conflicts, uneven scaling needs, different reliability requirements per service.
