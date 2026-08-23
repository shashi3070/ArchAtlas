# Patterns
Common interaction styles, each with a niche:

- **REST over JSON** - resources addressed by URLs; great fit for public APIs and CRUD. Cacheable by default when GET semantics are respected.
- **RPC (gRPC)** - contract-first, binary, strongly typed; efficient for internal service-to-service calls where both sides share schemas.
- **GraphQL** - clients shape responses in one query; reduces over-fetching for screen-driven apps at the cost of server-side query complexity.
- **Async/eventual** - long work is acknowledged with `202 Accepted`; results are polled or pushed later.

Rule of thumb: external APIs favor REST for reachability; internal hot paths favor gRPC for efficiency; anything longer than a user's attention span belongs behind an async pattern rather than a hanging HTTP request.
