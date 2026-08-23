# Tradeoffs
Aggressive timeouts reduce hang-risk but convert recoverable slowness into errors; too generous ties up threads and memory. Retries multiply load exactly during stress - budget them (retry budget: max X% extra traffic) and never retry non-idempotent operations blindly. Breakers flap when thresholds are tight; too loose and they're decorative.

Degradation needs product buy-in: engineers can serve stale prices, but business may forbid it. Document degradation modes explicitly per feature. Finally, redundancy halves availability math only if failure modes stay independent - shared config service or common DNS provider silently correlates everything.
