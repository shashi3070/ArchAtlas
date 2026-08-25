# Tradeoffs
**Client-side**: lower latency (no extra hop); client controls load balancing; harder to update all clients when the registry changes.
**Server-side**: simpler clients; extra network hop; load balancer becomes a bottleneck or SPOF.
**DNS**: universal support; slow to converge; limited to A/SRV records with no metadata.
**Consul/etcd**: rich metadata, health checks, and ACLs; operational complexity of running a cluster.

**When to prefer DNS**: simple environments with long-lived instances and low failover requirements.
