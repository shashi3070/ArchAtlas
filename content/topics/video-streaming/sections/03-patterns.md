# Patterns
- **Progressive upload**: chunked upload with resumability for large files.
- **Parallel transcoding**: split video into segments; transcode in parallel across workers.
- **Manifest stitching**: combine pre-transcoded segments into a new manifest without re-encoding.
- **CDN multi-tier**: origin → mid-tier CDN → edge CDN; tiered caching reduces origin load.
- **Quality of service**: prioritize popular content for caching; long-tail content served from origin.
- **Content fingerprinting**: detect copyright violations via video hashing.
