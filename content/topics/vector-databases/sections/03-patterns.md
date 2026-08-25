# Patterns
- **HNSW**: O(log N) search; high memory usage; best for <10M vectors.
- **IVF**: partition vectors into clusters; search only relevant clusters; good for >10M vectors.
- **Hybrid search**: combine vector similarity with keyword search (BM25).
- **Metadata filtering**: filter by attributes (e.g., `document_type = 'pdf'`) before vector search.
- **Multi-tenancy**: isolate vectors per tenant using namespace or collection.
- **Batch ingestion**: embed and index documents in batches for throughput.
