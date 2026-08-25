# How It Works
1. **Bounded buffer**: a queue with a fixed capacity sits between producer and consumer.
2. **Full buffer**: producer is signaled (blocked, gets an error, or oldest message is dropped).
3. **Pull-based**: consumer requests N messages; producer sends exactly N (reactive streams).
4. **Push-based with acknowledgment**: producer sends; consumer acknowledges; unacknowledged messages count against the buffer.
5. **Credit-based**: consumer gives the producer 'credits'; producer can only send when credits are available.

Kafka: consumer lag is the implicit backpressure signal; the broker holds messages until the consumer catches up.
