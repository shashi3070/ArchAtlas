# Tradeoffs
**Pros**: Sub-millisecond push latency; reduced HTTP overhead; natural bidirectional channel.
**Cons**: Stateful servers (harder to scale horizontally); connection management complexity; proxies/CDNs may not support WS; no built-in message ordering across reconnects.

**When to prefer SSE**: one-way server push (notifications, feeds) with simpler infrastructure.
**When to prefer gRPC streams**: service-to-service with typed contracts and bidirectional streaming.
