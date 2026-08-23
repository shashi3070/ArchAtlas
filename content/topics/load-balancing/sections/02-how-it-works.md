# How It Works
Request flow through an L7 proxy:

```
client -> LB :443 -> [pick backend] -> backend :8080
                        ^ health checks every N sec
```

Scheduling policies:

- **Round robin / weighted** - rotate through the pool; weights express capacity differences.
- **Least connections** - prefer backends with fewer open requests; adapts to variable request cost.
- **Consistent hashing** (on IP, cookie or header) - same key lands on the same backend, enabling server-local caches without sticky tables.
- **Random + power-of-two-choices** - sample two backends, pick the less loaded; near-optimal with almost no bookkeeping.

Health checks mark backends up/down. Active checks probe periodically; passive checks observe real failures (e.g., three consecutive 5xx) and eject the backend until it recovers.
