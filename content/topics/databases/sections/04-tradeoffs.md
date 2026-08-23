# Tradeoffs
Normalization reduces redundancy and update anomalies but forces joins; targeted denormalization (materialized views, counter columns) buys read speed at the price of write amplification and drift risk. Strong consistency simplifies code but serializes conflicting writes; relaxing to eventual consistency raises throughput and questions ("will my update be visible everywhere instantly?" - no).

Managed engines (RDS, Cloud SQL) remove backup/patch drudgery but cap configurability; self-managed clusters unlock extensions and tuning at ops cost. Sharding multiplies operational surface - backups, rebalancing, cross-shard transactions - so treat it as a last resort with clear evidence, not an architecture fashion statement.
