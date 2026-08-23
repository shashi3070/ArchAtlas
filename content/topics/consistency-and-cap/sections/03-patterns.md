# Patterns
- **Per-operation consistency selection**: checkout = strongly consistent; view counters = eventual; profile edit = read-your-writes.
- **Sticky reads for RYW**: pin a user's reads to the primary or an up-to-date replica for N seconds after their write.
- **Consensus for coordination**: leader election, locks, configuration - Raft/ZooKeeper/etcd, never homegrown heuristics.
- **CRDTs for collaborative state**: carts and presence merge without coordination, offline-tolerant.
- **Conflict UX**: when LWW is unacceptable, surface conflicts ("your edit clashed, merge manually") instead of silently dropping work.
