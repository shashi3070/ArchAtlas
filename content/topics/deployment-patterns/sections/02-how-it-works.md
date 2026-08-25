# How It Works
**Rolling**: update instances one at a time; old and new versions coexist temporarily; requires backward-compatible changes.
**Blue-green**: provision a full parallel environment (green); deploy new version there; switch load balancer to green; keep blue for rollback.
**Canary**: deploy new version to a small subset of instances; route 1-5% of traffic there; monitor error rates and latency; gradually increase.
**Feature flags**: deploy new code with a flag check; toggle the flag via config service to activate for specific users, regions, or percentages.
