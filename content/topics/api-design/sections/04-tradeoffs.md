# Tradeoffs
**REST**: widely understood, cacheable, tooling-rich; can be verbose; chatty for complex queries.
**GraphQL**: flexible queries, single endpoint; harder to cache, N+1 query risk, learning curve.
**gRPC**: high performance, streaming, typed contracts; browser support requires gRPC-web proxy.
**Versioning via headers**: clean URLs; invisible to casual debugging.
**Versioning via query param**: explicit but clutters URL; can be forgotten.

**When to prefer REST**: public APIs, CRUD-heavy domains, teams familiar with HTTP.
**When to prefer GraphQL**: mobile apps with varying data needs, many related entities.
