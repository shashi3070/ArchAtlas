# Patterns
- **Tiered quotas**: anonymous/IP < free key < paid < partner - monetization aligned with protection.
- **Weighted costs**: expensive endpoints consume multiple tokens reflecting compute spent.
- **Concurrency caps**: semaphores on expensive operations (exports, searches) bound simultaneous heavy work beyond rate.
- **Adaptive limits**: AIMD-style tightening on saturation signals (latency, error rate) auto-tunes thresholds.
- **Graceful client guidance**: SDKs embed retry-after honoring; docs publish quota headers semantics.
