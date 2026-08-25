# Tradeoffs
**301 vs 302**: 301 is cached by browsers (good for analytics, bad for changing URLs); 302 forces re-lookup.
**Random vs counter**: random is simpler but requires collision checks; counter is guaranteed unique but requires coordination.
**SQL vs NoSQL**: SQL for ACID and JOINs (analytics); NoSQL for horizontal scale and simple key-value lookups.

**When to prefer random codes**: low-traffic, simple deployment, no analytics requirements.
**When to prefer counters**: high-traffic, guaranteed uniqueness, no collision overhead.
