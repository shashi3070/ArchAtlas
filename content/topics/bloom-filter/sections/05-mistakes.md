# Common Mistakes
- **Too few bits**: false positive rate climbs above acceptable threshold.
- **Too many hash functions**: increases computation without proportional accuracy gain.
- **Not accounting for deletion**: standard bloom filters cannot remove elements; use counting bloom filters.
- **Shared bloom filter across partitions**: false positive rate compounds; use per-partition filters.
- **Ignoring growth**: filter sized for 1M elements will have high false positive rate at 10M elements.
