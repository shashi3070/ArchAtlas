# Patterns
- **HATEOAS**: include links to related resources in responses for discoverability.
- **Sparse fieldsets**: `?fields=id,name,email` to reduce payload size for mobile clients.
- **ETags**: return content hashes for conditional requests (`If-None-Match`) to save bandwidth.
- **Rate limiting headers**: `X-RateLimit-Remaining`, `Retry-After` to help clients back off gracefully.
- **Bulk endpoints**: `POST /orders/batch` with array payload to reduce round trips for mobile.
- **OpenAPI spec**: machine-readable API contract for code generation, docs, and validation.
