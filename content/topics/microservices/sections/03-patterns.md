# Patterns
- **API Gateway**: single entry point that handles routing, auth, rate limiting, and protocol translation.
- **Service Mesh**: sidecar proxies handle mTLS, retries, circuit breaking, and observability transparently.
- **Saga**: distributed transaction coordination via choreography or orchestration.
- **CQRS**: separate read and write models for different scaling profiles.
- **Strangler Fig**: incrementally replace monolith functionality with microservices.
- **Circuit Breaker**: prevent cascade failures when a downstream service is unhealthy.
