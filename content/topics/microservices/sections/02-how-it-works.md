# How It Works
1. Decompose by business capability (e.g., orders, payments, inventory), not by technical layer.
2. Each service exposes an API (REST, gRPC, or event-driven).
3. Each service owns its database; no direct cross-service DB queries.
4. Use API gateways for external routing; use service meshes for internal communication.
5. Distributed tracing, centralized logging, and health dashboards are mandatory.

Communication is synchronous (request/response) or asynchronous (events/messages). Mixed is common: commands use sync, events use async.
