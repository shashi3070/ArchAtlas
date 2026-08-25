# Tradeoffs
**Blocking**: simple; risks deadlock if the producer and consumer are in a cycle.
**Drop newest**: preserves order; loses the most recent data.
**Drop oldest**: preserves recent data; loses historical context.
**Credit-based**: precise control; complex protocol.

**When to prefer blocking**: when data loss is unacceptable (e.g., financial transactions).
**When to prefer dropping**: when fresh data is more important than completeness (e.g., metrics, logs).
