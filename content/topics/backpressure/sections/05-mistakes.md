# Common Mistakes
- **Unbounded buffers**: no backpressure mechanism; OOM is inevitable under load.
- **Blocking without timeout**: producer hangs forever waiting for buffer space.
- **Ignoring consumer lag**: Kafka consumer lag grows silently until it's unmanageable.
- **No monitoring**: backpressure events are invisible; you can't optimize what you can't measure.
- **Treating all messages equally**: high-priority messages should not be dropped alongside low-priority ones.
