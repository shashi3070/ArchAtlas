# How It Works
Delivery mechanics:

- **Mapping**: DNS/anycast routes users to optimal PoPs.
- **Caching keyed by URL+vary headers**; responses obey `Cache-Control` (max-age, s-maxage for shared caches, immutable) and validators (`ETag`, `Last-Modified`) driving conditional requests (304s).
- **Miss path**: PoP fetches from origin - ideally via a **shield tier** so one origin request populates all edges.
- **Invalidation**: purge APIs propagate deletion (seconds-minutes); versioned URLs (`app.9f2c.js`, `/v2/api/`) sidestep purging entirely.

Dynamic acceleration: connection pooling from PoP to origin (fewer handshakes), TCP optimization on long hauls, and optionally routing intelligence around congestion.
