# How It Works
1. **Ingestion**: documents are chunked (512-1024 tokens), embedded (text-embedding-3-small), and stored in a vector database.
2. **Retrieval**: user query is embedded, then top-K similar chunks are retrieved (K=5-20).
3. **Reranking**: a cross-encoder reranks retrieved chunks for relevance.
4. **Prompt construction**: retrieved chunks + user query are combined in a prompt template.
5. **Generation**: LLM generates a response grounded in the retrieved context.
6. **Post-processing**: extract citations, format response, apply safety filters.
