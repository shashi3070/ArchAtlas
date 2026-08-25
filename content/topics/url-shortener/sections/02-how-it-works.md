# How It Works
1. Client submits long URL via POST /shorten.
2. Server generates a short code (Base62-encoded counter or hash + collision check).
3. Mapping stored in DB: short_code → long_url + metadata (creator, expiry, analytics).
4. Redirect: GET /{code} → lookup in cache → if miss, lookup in DB → 301/302 redirect.
5. Analytics: log each redirect (timestamp, IP, referrer) for click tracking.

Components: API server, Redis cache, PostgreSQL/DynamoDB, CDN, analytics pipeline.
