# Patterns
- **Tiered balancing**: DNS or anycast steers regions; an L4 edge distributes connections; L7 proxies route within the region.
- **Service discovery integration**: backends register themselves (Consul, k8s endpoints); the balancer consumes the live list instead of static config.
- **Sticky sessions via consistent hashing** on a cookie - shopping carts and websockets benefit, but stickiness concentrates risk: losing a node loses its sessions' warmth.
- **Canary weighting**: shift 5% of traffic to a new version by weight, watch error rates, then ramp. The balancer is the deployment safety valve.
- **Connection draining**: on backend removal, stop *new* assignments but let in-flight requests finish - prevents error spikes during deploys.
