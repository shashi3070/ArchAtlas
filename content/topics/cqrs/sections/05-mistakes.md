# Common Mistakes
- **Applying CQRS to simple CRUD**: overengineering for low-traffic applications.
- **Ignoring eventual consistency**: UI shows stale data immediately after a write; users are confused.
- **No event versioning**: read models break when events change structure.
- **Synchronous event publishing**: if the event bus is down, the write side blocks.
- **Single read model for all queries**: different views need different projections; one model doesn't fit all.
