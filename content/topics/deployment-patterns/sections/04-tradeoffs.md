# Tradeoffs
**Rolling**: minimal infrastructure overhead; slow rollback (must re-roll); version skew during deploy.
**Blue-green**: instant rollback; doubles infrastructure cost; database migrations are complex.
**Canary**: low risk, fast feedback; requires sophisticated traffic routing and metrics.
**Feature flags**: deploy/release separation; flag debt accumulates; testing complexity increases.

**When to prefer canary**: high-traffic services where catching issues early is critical.
**When to prefer blue-green**: financial or safety-critical systems requiring instant rollback.
