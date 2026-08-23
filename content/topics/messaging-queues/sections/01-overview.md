# Overview
Queues turn synchronous chains into resilient pipelines. Instead of service A blocking on service B, A publishes a message and continues; B consumes whenever ready. Consequences:

- **Availability composition improves**: brief B downtime delays work instead of failing user requests.
- **Load leveling**: a flash sale enqueues 100k jobs; workers process at steady pace.
- **Independent scaling**: worker count tracks queue depth, not frontend traffic.

Brokers differ mainly in delivery model: **SQS/RabbitMQ** push tasks to competing consumers (work queues), **Kafka** retains ordered logs consumed at readers' own offset (streams, replayable), **Pub/Sub topics** fan out to every subscriber (notifications). Choosing wrong shows up as either lost work (no retention) or surprise duplicates (replay).
