# Tradeoffs
**Latency vs throughput**: smaller batches = lower latency; larger batches = higher throughput.
**Quantization vs quality**: INT4 is 4x faster but may lose nuance on complex tasks.
**Self-hosted vs API**: self-hosted gives control and lower cost at scale; API is simpler.

**When to prefer API**: low volume; need access to latest models;不想管理GPU.
**When to prefer self-hosted**: high volume; data privacy requirements; cost optimization.
