# Overview
Replication exists for fault tolerance and locality - copies of data on multiple machines. The moment copies exist, they can disagree. **Consistency models** name the agreement level clients may expect:

- **Strong / linearizable**: every read sees the latest completed write, as if one machine existed.
- **Sequential**: operations respect program order per process, global order may differ from real time.
- **Read-your-writes**: you always see your own updates; others may lag.
- **Eventual**: replicas converge eventually; windows of contradiction allowed.

CAP states the trilemma: under a **network partition**, choose **consistency** (refuse operations that could diverge) or **availability** (serve possibly stale/divergent). Partitions are rare-but-certain, so the real design act is deciding per operation what fails ugliest: wrong answers or unavailable ones.
