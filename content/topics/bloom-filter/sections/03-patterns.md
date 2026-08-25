# Patterns
- **Database check-before-read**: bloom filter on disk; skip SSTable lookup if filter says 'not present' (LevelDB, Cassandra).
- **Cache stampede prevention**: bloom filter tracks in-flight requests to coalesce duplicate misses.
- **Web crawler dedup**: bloom filter of visited URLs; skip revisits with <1% false positive.
- **Ad-blocker**: bloom filter of known ad domains; fast lookup in the browser extension.
- **Network routers**: bloom filter of banned IPs for O(1) membership check.
- **Cuckoo filter**: supports deletion; better space efficiency for small sets.
