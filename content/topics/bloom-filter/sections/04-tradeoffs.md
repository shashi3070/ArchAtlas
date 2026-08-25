# Tradeoffs
**Pros**: O(k) lookup; extremely space-efficient; no false negatives; simple implementation.
**Cons**: False positives; no deletion (standard); no stored elements (can't enumerate); accuracy degrades as filter fills.

**When to prefer**: high-throughput membership testing where a small false positive rate is acceptable and memory is constrained.
**When to prefer a hash set**: exact membership required; small set size; memory is not constrained.
