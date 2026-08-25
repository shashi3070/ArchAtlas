# How It Works
1. Client acquires lock: `SET lock_key {uuid} NX PX 30000` (TTL prevents deadlock on crash).
2. Client performs the protected operation.
3. Client releases lock: only if the UUID matches (Lua script for atomicity).
4. If lock expires before release, another client acquires it; the first client must not proceed.

**Safety property**: at most one client holds the lock at any time.
**Liveness property**: lock is eventually released (TTL) and acquisition is possible (no permanent blocking).
