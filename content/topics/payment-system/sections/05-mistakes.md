# Common Mistakes
- **No idempotency**: duplicate charges from retries.
- **Single-entry bookkeeping**: impossible to reconcile; financial discrepancies undetectable.
- **Ignoring webhook ordering**: out-of-order status updates corrupt state.
- **No reconciliation**: discrepancies between internal ledger and gateway go unnoticed.
- **Storing card data**: PCI compliance requires tokenization; never store raw card numbers.
