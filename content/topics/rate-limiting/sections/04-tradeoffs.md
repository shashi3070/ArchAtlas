# Tradeoffs
Strict limits annoy legitimate power users; loose ones enable hogging. Per-IP limits punish shared NATs (offices, mobile carriers) - combine with account/key identity. Centralized counters (Redis) give global precision but add a hot-path dependency; local approximate limits scale better but undercount globally. Rejection UX matters: queued waiting, degraded responses, or hard 429s each suit different products.

Security layering complements rate limiting: WAF filters attack signatures, bot management scores automation, authentication gates identity - limiting is necessary but insufficient alone. Monitor limit-hit metrics per key: spikes reveal either abuse or your own buggy client loops.
