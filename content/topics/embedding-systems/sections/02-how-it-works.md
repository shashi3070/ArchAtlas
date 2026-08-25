# How It Works
1. **Input**: text is tokenized and passed through a transformer model.
2. **Pooling**: token embeddings are pooled (mean pooling or CLS token) to a single vector.
3. **Normalization**: vectors are L2-normalized for cosine similarity.
4. **Output**: a dense vector of fixed dimensions (e.g., 1536).
5. **Storage**: vectors are stored in a vector database with metadata.
6. **Query**: query text is embedded, then similarity search finds the most similar vectors.

Models: OpenAI text-embedding-3, Cohere embed-v3, sentence-transformers (all-MiniLM-L6-v2).
