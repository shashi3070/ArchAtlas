# How It Works
Token bucket: bucket holds up to B tokens refilling at rate r; each request consumes one (or weight w); empty bucket rejects. Burst tolerance = B, sustained = r - one mechanism expressing both. Sliding-window counters approximate exact logs with two adjacent fixed windows weighted by elapsed fraction - O(1) memory per key.

Placement mechanics: edge limiters run in CDN/gateway (Cloudflare, NGINX `limit_req`, Envoy ratelimit service) using fast stores; service-level limiter libraries consult shared Redis with Lua atomicity. Responses must teach clients: `429` + `Retry-After` (+ `X-RateLimit-Remaining/-Reset`). Prioritized shedding under extreme load drops lowest tiers first (batch < free < paid < critical).
