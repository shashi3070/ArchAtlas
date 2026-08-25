# How It Works
1. **Client initiates payment**: POST /payments with idempotency key.
2. **Payment service**: validates request, creates pending ledger entry, calls payment gateway (Stripe).
3. **Gateway processes**: charges the card and returns a transaction ID.
4. **Ledger update**: debit sender account, credit receiver account (double-entry).
5. **Webhook**: gateway sends status update; service reconciles with internal state.
6. **Reconciliation**: periodic batch job compares internal ledger with gateway statements.

Components: payment service, ledger service, gateway adapter (Stripe/PayPal), reconciliation service, notification service.
