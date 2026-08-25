# How It Works
1. **Embedding**: text/image is converted to a vector (e.g., 1536 dimensions for OpenAI embeddings).
2. **Indexing**: vectors are indexed using ANN algorithms (HNSW, IVF, LSH).
3. **Query**: a query vector is embedded, then the index finds the K nearest neighbors.
4. **Filtering**: metadata filters (e.g., document type, date) are applied before or during search.
5. **Storage**: vectors are stored with metadata (document ID, chunk text, etc.).

Vector DB options: Pinecone (managed), Weaviate (open-source), Qdrant (open-source), pgvector (PostgreSQL extension), Milvus (open-source).
