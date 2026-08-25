# Common Mistakes
- **Events as commands**: events should be facts that happened, not instructions to do something.
- **No event versioning**: schema changes break existing projections.
- **Storing PII in events**: events are immutable; PII removal requires event deletion or encryption.
- **No snapshot strategy**: replaying millions of events on every query is slow.
- **Tight coupling to event store**: projections should be replaceable; don't query the event store directly for reads.
