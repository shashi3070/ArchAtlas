# Common Mistakes
- **No metadata filtering**: returning irrelevant results from wrong document types.
- **Ignoring index build time**: HNSW index build is slow; plan for it.
- **Wrong distance metric**: cosine for text, L2 for images; using the wrong metric gives poor results.
- **No chunk deduplication**: duplicate chunks waste storage and bias results.
- **No evaluation**: measuring recall@K and precision@K is essential.
