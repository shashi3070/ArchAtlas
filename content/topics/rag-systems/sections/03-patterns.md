# Patterns
- **Hybrid search**: combine vector similarity (semantic) with BM25 (keyword) for better recall.
- **Hierarchical indexing**: summaries at top level, detailed chunks at bottom; retrieve at the right level.
- **Query expansion**: generate multiple query variations to improve recall.
- **Self-RAG**: LLM decides when to retrieve and when to rely on parametric knowledge.
- **Corrective RAG**: validate retrieved chunks; re-retrieve if quality is low.
- **Multi-modal RAG**: embed images, tables, and code alongside text.
