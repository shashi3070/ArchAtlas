# Patterns
- **Sequence ID**: monotonic counter per conversation; ensures ordering even across servers.
- **Fan-out on write**: pre-compute group member lists; write to each member's inbox.
- **Fan-out on read**: store message once in group feed; each reader computes their view.
- **End-to-end encryption**: client-side encryption; server stores ciphertext only.
- **Message deduplication**: idempotency key per message; retry-safe delivery.
- **Receipts**: delivered (server ack) and read (client ack) receipts for UX.
