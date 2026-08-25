# Patterns
- **Health-check layers**: Liveness (is the process alive?) vs. readiness (can it serve traffic?). Both must pass for the instance to receive traffic.
- **Sidecar proxy**: a local agent (Envoy, Consul Connect) handles discovery, routing, and mTLS so the application doesn't need a discovery library.
- **DNS SRV records**: map `_service._proto.domain` to `port weight priority target`; combined with health checks for automatic failover.
- **Eventual consistency**: most registries are CP (etcd, Consul with Raft); reads may lag writes by one heartbeat interval.
- **Graceful shutdown**: deregister before stopping to avoid serving 502s during the TTL window.
