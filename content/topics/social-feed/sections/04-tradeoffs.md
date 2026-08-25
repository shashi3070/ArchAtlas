# Tradeoffs
**Fan-out-on-write**: O(1) read; O(followers) write; stale feeds if cache is not refreshed.
**Fan-out-on-read**: O(1) write; O(following) read; expensive for users following many accounts.
**Hybrid**: best of both; complex to maintain; two code paths.

**When to prefer fan-out-on-write**: small social networks; read-heavy workload.
**When to prefer fan-out-on-read**: large networks with celebrity accounts; write-heavy workload.
