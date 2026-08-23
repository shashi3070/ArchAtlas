# Tradeoffs
Long TTLs maximize offload but complicate emergency fixes - purge pipelines must be rehearsed. Edge compute introduces a new runtime to debug with eventual-consistency semantics for shared state. Multi-CDN doubles configuration surface (headers, WAF rules drift). Vendor egress pricing rewards aggressive caching and punishes chatty dynamic routing through the CDN.

Security posture shifts too: TLS termination at edge means private keys live with the vendor (or use BYOIP/keyless). DDoS absorption is a CDN superpower, but misconfigured origin direct-IP access bypasses it - lock origin ingress to provider ranges.
