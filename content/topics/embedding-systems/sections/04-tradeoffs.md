# Tradeoffs
**Model size**: larger models = better quality but slower inference and more memory.
**Dimension**: higher dimensions = better quality but slower search and more storage.
**API vs local**: API is easier but adds latency and cost; local is faster but requires GPU.

**When to prefer API**: low volume; don't want to manage GPU infrastructure.
**When to prefer local**: high volume; data privacy requirements; latency-sensitive.
