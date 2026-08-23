# Mistakes
Frequent beginner errors:

- **Chatty APIs** - rendering one screen fires dozens of tiny requests. Batch or nest instead.
- **Ignoring status codes** - returning `200 OK` with an error payload breaks proxies, retries and monitoring.
- **Hidden state in the URL or memory** - sessions vanish when a pod restarts; keep state in a shared store.
- **No timeout anywhere** - a slow dependency then hangs every caller forever. Always set connect/read timeouts explicitly.
- **Assuming LAN latency** - cross-region round trips are tens of milliseconds; design locality accordingly.
