# How It Works
Mechanisms enforcing models:

- **Leader-based replication**: all writes to a leader, followers replicate; reads from leader = strong-ish, from followers = eventual. Failover elects a new leader via quorum consensus (Raft/Paxos).
- **Quorums (Dynamo-style)**: N replicas, write W, read R with W+R>N ensures read-write overlap. Tune W=R=3,N=5 for durability with tolerance of one node loss.
- **Versioning & anti-entropy**: vector versions detect conflicts; CRDTs merge deterministically (counters, sets); last-write-wins silently drops concurrent edits.

Latency hides in the acronym PACELC: **i**f **P**artition choose A or C, **e**lse (normal operation) choose latency or consistency - quorum reads cost a round trip to the fastest quorum, so stronger models pay runtime tax even without failures.
