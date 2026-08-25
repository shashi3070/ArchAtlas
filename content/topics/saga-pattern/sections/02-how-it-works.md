# How It Works
**Choreography-based**:
1. Order Service creates order → publishes `OrderCreated`.
2. Payment Service receives event → charges payment → publishes `PaymentProcessed`.
3. Inventory Service receives event → reserves stock → publishes `StockReserved`.
4. If stock reservation fails → publishes `StockReservationFailed` → Payment Service refunds.

**Orchestration-based**:
1. Order Orchestrator tells Payment Service to charge.
2. On success, tells Inventory Service to reserve.
3. On failure, tells Payment Service to refund.

Each step must define: execute (forward) and compensate (undo).
