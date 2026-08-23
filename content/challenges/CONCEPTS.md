# Challenge Concepts — Phase 0 Exit Deliverable

Status: **concepts defined** (24 concepts, ≥20 exit criterion met).
Implementation begins in Phase 4 per `PLAN.md` §18.

Each concept becomes a **progressive chain** (URL-shortener L1–L6 pattern,
`SYSTEM.md` §27): levels scale the workload and unlock new concepts.
Chains + Repair Drills yield 45–60 playable challenges at Phase 4 exit.

| # | Family | Difficulty ramp | Core concepts taught |
|---|--------|-----------------|----------------------|
| 1 | Static website hosting | B → I | CDN, caching headers, origin offload |
| 2 | Three-tier web application | B → I | LB, stateless API, relational DB |
| 3 | URL shortener | B → A | read-heavy scaling, hashing, cache-aside |
| 4 | Rate limiter service | I | token bucket, Redis atomic ops, hot keys |
| 5 | Notification system | I → A | queues, async delivery, retries, DLQ, idempotency |
| 6 | Chat system (1:1 + group) | I → A | websockets, fan-out, message ordering, presence |
| 7 | File storage (Dropbox-lite) | I | object storage, presigned uploads, dedup |
| 8 | Image processing pipeline | I → A | workers, queue buffering, resize farm |
| 9 | Video streaming platform | A | transcoding, CDN, adaptive bitrate, storage tiering |
| 10 | Search system | I → A | inverted index store, indexing pipeline lag |
| 11 | News feed | A | fan-out on write vs read, ranking cache, celebrity problem |
| 12 | Payment system | E | strong consistency, idempotency, ledger, exactly-once |
| 13 | Job queue platform | I | competing consumers, backpressure, priorities |
| 14 | Metrics/time-series system | A | write-heavy ingestion, downsampling, retention |
| 15 | Distributed cache service | E | consistent hashing, eviction, replication, hot key |
| 16 | Webhook delivery system | I → A | at-least-once, retry with backoff, dead letters, signing |
| 17 | Feature-flag service | I | read-heavy, low latency, eventual consistency tolerance |
| 18 | Leaderboard service | I | sorted sets, write contention, sharding by game |
| 19 | Live comments widget | A | websocket fan-in/out, backpressure, region affinity |
| 20 | Ride-hailing dispatch (geo) | E | geo-indexing, matching latency, partition by city |
| 21 | Ad-click aggregator | E | massive writes, stream aggregation, approximate counts |
| 22 | Collaborative document service | E | CRDT/OT trade-offs, sync protocol, presence |
| 23 | RAG knowledge assistant | A | embeddings, vector DB, retrieval latency, guardrails |
| 24 | Multi-model AI gateway | E | routing, quotas, fallbacks, token cost control |

## Repair Drills (Repair Mode)

Derived programmatically from golden architecture fixtures by removing or
corrupting exactly one property/connection. Each drill: symptom brief with
telemetry-style numbers → learner fixes → deterministic re-evaluation.
Initial drill seeds (one per flaw):

1. URL shortener missing cache under 80% reads
2. Notification system calling provider synchronously
3. Chat system single websocket gateway instance
4. Payments reading from replica (stale balance)
5. Job queue without DLQ
6. API retries without timeout/backoff
7. Static site bypassing CDN for images
8. Feed fan-out writing to single DB primary at 100K RPS
9. Rate limiter storing counters in local memory only
10. HA setup with replicas but no automatic failover

## Golden Architecture Fixtures (testing bedrock)

Each family ships ≥2 fixtures: `good` and one or more `broken-*`
(single-DB SPOF, overloaded DB, missing cache, async/sync violation…).
See `PLAN.md` §16.4 and `tests/golden_architectures/`.
