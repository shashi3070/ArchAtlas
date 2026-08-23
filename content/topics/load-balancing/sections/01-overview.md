# Overview
A load balancer sits between clients and a pool of servers, forwarding each request to a backend chosen by some policy. Two jobs, really:

1. **Throughput** - no single server saturates while others idle.
2. **Availability** - dead servers stop receiving traffic before users notice.

Balancers operate at different layers. An **L4** balancer routes TCP connections by IP/port - extremely fast, blind to content. An **L7** balancer terminates and re-originates HTTP, letting it route `/api/*` to one pool and images to another, rewrite headers, or stick sessions. Managed clouds offer both flavors (NLB vs ALB on AWS); self-hosted fleets commonly run HAProxy, NGINX or Envoy.
