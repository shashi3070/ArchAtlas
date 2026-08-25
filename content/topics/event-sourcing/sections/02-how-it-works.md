# How It Works
1. **Command**: a client sends a command (e.g., `PlaceOrder`).
2. **Aggregate**: validates the command against current state (replayed from events).
3. **Event**: if valid, emits `OrderPlaced` and appends it to the event store.
4. **Projection**: event subscribers update read models (e.g., order list view, analytics dashboard).
5. **Snapshot**: periodically save the derived state to avoid replaying the full log.

Event store: EventStoreDB, Kafka (as a log), PostgreSQL with an events table, or DynamoDB.
