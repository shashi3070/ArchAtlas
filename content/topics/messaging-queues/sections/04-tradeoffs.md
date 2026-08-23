# Tradeoffs
Asynchrony buys resilience with eventual consistency: users see "processing..." and data converges later - product flows must tolerate that. Kafka's log gives replay, ordering-per-partition and high throughput, demanding operational care (partition planning, retention sizing). SQS-style queues are operationally trivial but forget delivered messages, so replay means re-producing.

Visibility timeouts vs leases vs manual acks trade stuck-message recovery against duplicate work. Long-lived connections to brokers become hidden dependencies: deploy rolling consumers carefully so partitions rebalance without storms. And remember messages are schema contracts too - evolve them with versioning discipline like any API.
