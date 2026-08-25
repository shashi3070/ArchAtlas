# How It Works
1. Each service instance registers itself with the discovery server on startup (HTTP POST or gRPC call).
2. The instance sends periodic heartbeats (TTL refresh) or the server probes a health endpoint.
3. On failure, the server marks the instance unhealthy and removes it from lookups.
4. Clients either query the registry directly (client-side) or send traffic to a known VIP/load balancer that queries the registry (server-side).

Registration can be push (instance registers) or pull (server probes a well-known endpoint like `/health`).
