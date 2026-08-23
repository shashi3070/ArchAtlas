# Tradeoffs
Full tracing everywhere is expensive (sampling!); head-based sampling keeps fixed %, tail-based keeps interesting traces (slow/errorful) at higher backend cost. High-cardinality labels empower debugging and bankrupt TSDBs - draw the line consciously. Third-party SaaS observability accelerates onboarding but bills per host/GB and ships data externally; self-hosted stacks cost ops time instead.

Log retention balances forensics against cost: hot (searchable, 7-14d), warm (compressed, 90d), cold archive (compliance). Alert fatigue is a reliability bug in itself - every noisy alert trains on-call to ignore pages; prune aggressively.
