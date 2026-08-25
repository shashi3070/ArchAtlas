# Patterns
- **Idempotency keys**: client-generated UUID per payment; server stores result for 24h.
- **Double-entry ledger**: every transaction has a debit and credit entry; balances are derived.
- **Saga**: payment + ledger update as a saga; compensation = refund + reverse ledger entry.
- **Ledger partitioning**: partition by account ID for horizontal scaling.
- **Webhook verification**: validate HMAC signature; reject unsigned webhooks.
- **Reconciliation**: daily batch comparing internal ledger vs gateway settlement files.
