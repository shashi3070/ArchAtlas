# Tradeoffs
**Chunk size**: smaller chunks = more precise retrieval but lose context; larger chunks = better context but noisy retrieval.
**K value**: higher K = more context but more noise and cost; lower K = faster but may miss relevant info.
**Embedding model**: larger models = better quality but slower and more expensive.

**When to prefer RAG over fine-tuning**: when data changes frequently; when citations are needed; when you can't afford to fine-tune.
**When to prefer fine-tuning**: when you need the model to learn a specific style or format.
