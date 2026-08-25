# Common Mistakes
- **No heartbeat**: zombie connections accumulate; server以为 client is alive.
- **Unbounded buffers**: slow clients cause OOM on the server.
- **Missing reconnection logic**: client assumes connection is permanent.
- **Broadcasting to all connected clients**: use rooms/channels instead.
- **Ignoring WebSocket security**: always validate Origin; use wss:// (TLS) in production.
