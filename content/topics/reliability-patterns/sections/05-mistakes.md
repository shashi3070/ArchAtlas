# Mistakes
- **Default infinite timeouts** in HTTP clients - the top cause of cascading stalls.
- **Retry at every layer** - 3 layers x 3 attempts = 27x amplification; centralize policy per hop.
- **Breakers without fallback** - opening circuits just surfaces errors faster without protecting UX.
- **Shared everything** - one connection pool, thread pool or AZ for all dependencies invites correlated collapse.
- **Untested failover** - standby systems rot; drill promotion quarterly or discover rot during incidents.
