# Mistakes
- **Non-idempotent consumers** - double-charging on redelivery; fix with dedupe keys at the sink.
- **Unbounded in-flight work** - workers prefetch thousands then die; limit prefetch to what crash-recovery tolerates.
- **Hot partitions** - celebrity user id as key starves one shard; bucket hot keys.
- **Silent DLQs** - dead letters pile up unread; alarm on DLQ depth like production traffic.
- **Using queues as databases** - retention expires, data vanishes; durable state belongs in a store.
