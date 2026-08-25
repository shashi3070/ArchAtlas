# Overview
A URL shortener maps long URLs to short, human-readable codes. The core challenge is generating unique short codes at scale, serving redirects with minimal latency, and maintaining URL mappings durably.

Read traffic dominates (100:1 read-to-write ratio), so the system is optimized for fast reads via caching and CDN, while writes are handled by a smaller set of origin servers.
