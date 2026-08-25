# Common Mistakes
- **Fan-out-on-write for celebrities**: 10M writes per post overwhelms the system.
- **No feed length limit**: feeds grow unbounded; paginate and truncate.
- **Synchronous fan-out**: one slow follower delays posting for everyone.
- **No ranking**: chronological feeds miss relevant content; ML ranking improves engagement.
- **Ignoring duplicate posts**: a shared post appears in both fan-out and celebrity live merge.
