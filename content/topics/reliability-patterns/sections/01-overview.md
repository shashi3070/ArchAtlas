# Overview
Distributed systems fail partially, constantly. Reliability engineering assumes failure and shapes its blast radius. Four primitives do most of the work:

- **Timeout** - every remote call carries a deadline; waiting forever converts one slow dependency into total outage.
- **Retry** - transient faults recover on second attempt; unbounded or synchronized retries amplify outages.
- **Circuit breaker** - track failure rate per dependency; when it trips, fail immediately for a cool-down window, then trial half-open.
- **Fallback/degradation** - answer with cached data, defaults, or hide the feature - worse-than-normal beats nothing-at-all.

These compose into a posture: fail fast, degrade visibly, recover automatically, alert honestly.
