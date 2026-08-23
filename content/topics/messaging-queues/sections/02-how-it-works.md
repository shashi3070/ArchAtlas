# How It Works
Lifecycle: produce -> persist -> deliver -> process -> **acknowledge**. The acknowledgment is the contract's pivot. If the consumer crashes before acking, the broker redelivers - so honest guarantees are:

- **At-most-once** - fire and forget; loss possible, duplicates impossible. Fine for metrics ticks.
- **At-least-once** - redelivery until acked; duplicates possible. The workhorse; pair with idempotency.
- **Exactly-once** - achievable within bounded scopes (Kafka transactions end-to-end on one cluster); costly and never magic across arbitrary sinks.

Consumers coordinate via **consumer groups**: partitions/queues assign to members, scaling by adding members up to partition count. Poison messages need a **DLQ** after N attempts so one bad payload cannot clog the pipeline.
