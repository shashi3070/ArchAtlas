# Patterns
- **Event versioning**: tag events with a version; upcasters transform old versions on read.
- **Snapshotting**: every N events, save state snapshot; replay starts from snapshot.
- **Compaction**: merge old events into a summary (e.g., `AccountOpened` + 100 `MoneyDeposited` → `BalanceSnapshot`).
- **Rebuild projections**: delete a read model and replay from scratch to fix bugs or add new views.
- **Temporal queries**: `getStateAt(timestamp)` by replaying events up to that point.
- **Event bus integration**: publish events to Kafka/SNS for cross-service consumption.
