# How It Works
1. **Seed URLs**: start with a set of known URLs.
2. **URL frontier**: prioritize URLs; enforce politeness (max 1 request/second per domain).
3. **Fetcher**: download page content; respect robots.txt; handle redirects.
4. **Parser**: extract links; add new URLs to frontier; extract content for indexing.
5. **Deduplication**: compute URL hash + content fingerprint; skip duplicates.
6. **Storage**: store fetched pages in object storage; update search index.

Components: URL frontier (Redis/Kafka), fetcher cluster, parser, dedup service (bloom filter + content hash), page store (S3), robots.txt cache.
