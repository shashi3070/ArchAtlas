# Patterns
- **URL frontier with priority**: high-priority pages (homepages, news) crawled first.
- **Politeness**: per-domain rate limiting; DNS cache to avoid repeated lookups.
- **Bloom filter dedup**: URL-level dedup with bloom filter; content-level with simhash.
- **Distributed crawling**: partition URLs by domain hash across fetcher machines.
- **Incremental crawl**: re-crawl pages based on freshness signals (change frequency).
- **Trap avoidance**: limit crawl depth; detect URL patterns that generate infinite pages.
