# Common Mistakes
- **No message ordering**: messages appear out of order on the recipient's device.
- **Acknowledging before persistence**: message ack'd but server crashes before write = lost message.
- **Unbounded offline queue**: user offline for days; queue grows unbounded.
- **No presence timeout**: stale 'online' indicators mislead users.
- **Synchronous fan-out**: one slow group member delays delivery to all others.
