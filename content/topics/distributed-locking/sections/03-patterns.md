# Patterns
- **Fencing tokens**: lock includes a monotonically increasing token; the resource server rejects writes with stale tokens.
- **Redlock**: acquire locks on N/2+1 independent Redis masters; controversial due to timing assumptions.
- **Optimistic concurrency**: version numbers or CAS instead of locks; avoids lock overhead entirely.
- **Lease-based**: lock is tied to a lease that expires; holder must renew or lose it.
- **Lock hierarchy**: acquire locks in a consistent global order to prevent deadlocks.
- **Non-blocking**: try-lock with timeout instead of blocking; avoids thread starvation.
