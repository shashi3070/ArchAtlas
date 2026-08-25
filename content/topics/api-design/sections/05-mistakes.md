# Common Mistakes
- **Inconsistent naming**: mixing `camelCase` and `snake_case` in the same API.
- **Returning 200 for errors**: clients can't distinguish success from failure programmatically.
- **No rate limiting**: one abusive client can exhaust server resources.
- **Leaking internals**: stack traces, SQL errors, or internal IDs in error responses.
- **Breaking changes without versioning**: renaming fields or removing endpoints breaks existing consumers.
- **No idempotency for financial operations**: duplicate requests create duplicate charges.
