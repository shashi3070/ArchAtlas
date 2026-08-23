# Tradeoffs
Strong consistency centralizes serialization points - throughput ceilings and regional latency (writes wait for cross-region quorum). Eventual consistency scales writes horizontally and survives partitions gracefully but leaks anomalies to users unless product flows anticipate them (double-submit buttons, optimistic UI with rollback).

Durability is adjacent but distinct: N=3 with W=2 survives one replica loss synchronously. Cross-region active-active maximizes availability yet guarantees conflict-resolution logic in the app. Most teams discover they need strong consistency in far fewer places than assumed - find those places precisely, relax everywhere else.
