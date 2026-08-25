# Tradeoffs
**Storage vs quality**: higher resolutions need more storage; 4K is 10x larger than 720p.
**Transcoding cost vs latency**: immediate transcoding is expensive; batch transcoding is cheaper but delays availability.
**CDN cost vs latency**: more edge nodes reduce latency but increase cost.

**When to prefer client-side transcoding**: live streaming with low latency; limited storage.
**When to prefer server-side transcoding**: VOD with quality requirements; storage is cheap.
