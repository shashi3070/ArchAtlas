# Mistakes
- **Health-check theater** - probing `/healthz` that only answers "ok" without checking DB connectivity marks zombies as alive. Probe meaningfully.
- **Uneven connection pools** - if every app instance opens persistent connections, round-robin per *request* still skews per-*server* load; consider least-outstanding-requests.
- **Forgetting the balancer scales too** - a single HAProxy box is the new SPOF; run pairs with VRRP or use managed anycast.
- **Retry storms** - naive retries at the balancer plus retries in clients multiply load exactly when the system is dying. Budget retries end-to-end.
- **Session affinity hiding state bugs** - sticky sessions mask missing shared state; disable them in staging to catch it early.
