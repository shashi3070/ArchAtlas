# Tradeoffs
**Redis locks**: fast (sub-ms); risk of loss on failover; Redlock adds safety at the cost of latency.
**ZooKeeper locks**: strong consistency (ZAB); higher latency (~10ms); operational complexity.
**Database locks**: strong consistency; slower than Redis; scales with the DB.

**When to prefer optimistic concurrency**: contended-but-not-hot resources; lower latency.
**When to prefer distributed locks**: exclusive resources where a race causes data corruption or financial loss.
