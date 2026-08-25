# Patterns
- **Connection affinity**: route users to the server holding their WebSocket via consistent hashing on user ID; sticky sessions at the load balancer.
- **Fan-out via pub/sub**: each WS server subscribes to a Redis/NATS channel per room; messages published to the channel fan out to all subscribers.
- **Heartbeat + idle timeout**: send ping every 30s; close after 3 missed pongs.
- **Backpressure**: if a client consumes slowly, buffer with a bounded queue and drop or pause the slowest consumers.
- **Reconnect with jitter**: client retries with exponential backoff + random jitter to avoid thundering herd.
