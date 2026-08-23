# Mistakes
- **Caching uncacheables** - per-user data stored under a global key leaks information; include identity in the key or don't cache.
- **Unbounded local caches** - in-process dicts grow until OOM; always cap and measure.
- **Serializing whales** - storing megabyte objects wastes memory and network; store normalized, small values.
- **No stampede defense on hot keys** - celebrity profiles expire and flatten the DB. Use stale-while-revalidate or jittered TTLs.
- **Treating cache as durable** - Redis restart = empty namespace; anything not recoverable from the store is lost forever.
