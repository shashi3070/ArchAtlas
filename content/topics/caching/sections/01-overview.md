# Overview
A cache keeps a copy of data nearer to where it is used, betting that the same data will be asked for again before it changes. When the bet wins, latency drops from disk/network speeds to memory speeds and the backing store is shielded from load.

Caching appears at every layer: browser and CDN cache HTTP responses; reverse proxies cache full pages; Redis or Memcached cache query results and objects; CPU hardware caches microsecond-scale data. All share the same core questions: *what* to cache, *how long* to trust it, and *what happens when the copy goes stale*.

Because a cache serves possibly-outdated copies, correctness thinking shifts from "is this true?" to "is stale acceptable, and for how long?" - a business question, not just a technical one.
