# Common Mistakes
- **Not normalizing**: cosine similarity requires L2-normalized vectors.
- **Wrong model for the task**: code embeddings for text search give poor results.
- **No batching**: embedding documents one at a time is 10x slower.
- **Ignoring dimension**: 768-dim vectors may not capture enough nuance for complex tasks.
- **No evaluation**: measuring retrieval quality (recall@K) is essential.
