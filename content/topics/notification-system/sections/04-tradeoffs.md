# Tradeoffs
**Push vs email**: push is instant but app-dependent; email is universal but slower.
**Single queue vs per-channel queues**: single queue is simpler; per-channel queues allow independent rate limiting.
**Synchronous vs asynchronous**: synchronous gives immediate delivery confirmation; async is more resilient.

**When to prefer synchronous**: critical notifications (security alerts).
**When to prefer asynchronous**: bulk notifications (marketing, newsletters).
