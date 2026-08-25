# Common Mistakes
- **No fencing token**: two clients believe they hold the lock after a network partition.
- **Locking too long**: holding a lock while doing slow I/O blocks all other clients.
- **Forgetting TTL**: a crashed client's lock blocks the resource forever.
- **Locking non-idempotent operations**: if the operation must be retried after lock loss, it may execute twice.
- **Assuming Redis is linearizable**: single Redis is CP-like but not truly linearizable; use Redlock or ZooKeeper for strong consistency.
