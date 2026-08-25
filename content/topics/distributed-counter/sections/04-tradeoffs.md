# Tradeoffs
**Exact vs approximate**: exact requires coordination (slow); approximate is fast but may be slightly off.
**Single vs sharded**: single is simple but a bottleneck; sharded distributes load but requires merge.
**Synchronous vs asynchronous**: synchronous is accurate; asynchronous is faster but stale.

**When to prefer exact**: financial counters (account balance).
**When to prefer approximate**: social metrics (likes, views) where slight inaccuracy is acceptable.
