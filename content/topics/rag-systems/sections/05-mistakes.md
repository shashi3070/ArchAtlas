# Common Mistakes
- **Poor chunking**: splitting mid-sentence loses context; use semantic chunking.
- **No reranking**: initial retrieval is noisy; reranking significantly improves precision.
- **Ignoring chunk metadata**: document title, section, and date should be included for context.
- **No evaluation**: measuring retrieval quality (precision@K, MRR) is essential before optimizing generation.
- **Static knowledge base**: knowledge goes stale; implement regular re-indexing.
