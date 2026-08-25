# Tradeoffs
**Synchronous vs async**: synchronous gives immediate confirmation; async is more resilient but requires webhook handling.
**Single ledger vs dual ledger**: single ledger for simplicity; dual ledger (internal + gateway) for reconciliation.
**Stripe vs self-hosted**: Stripe handles PCI compliance and fraud; self-hosted gives more control.

**When to prefer Stripe/PayPal**: startups, low volume, want to avoid PCI compliance.
**When to prefer self-hosted**: high volume, custom payment flows, multi-gateway support.
