# Common Mistakes
- **No rate limiting**: one user can flood the system with shortens.
- **Encoding leaking internal IDs**: sequential IDs reveal system volume and enable enumeration.
- **No expiry**: unused URLs accumulate forever, growing the DB unbounded.
- **Cache stampede on popular URLs**: one cache miss triggers hundreds of concurrent DB reads.
- **Ignoring HTTPS**: short URLs in emails with HTTP links are phishable.
