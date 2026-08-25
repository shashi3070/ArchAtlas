# Tradeoffs
**Managed vs self-hosted**: managed (Pinecone) is easier; self-hosted (Qdrant) gives control and cost savings.
**HNSW vs IVF**: HNSW is faster but uses more memory; IVF is more memory-efficient but slower.
**Dimensionality**: higher dimensions = better quality but slower search and more storage.

**When to prefer pgvector**: already using PostgreSQL; small-to-medium scale.
**When to prefer Pinecone/Qdrant**: high scale; need managed infrastructure.
