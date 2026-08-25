# Patterns
- **Mean pooling**: average token embeddings; simple and effective.
- **CLS token**: use the classification token embedding; common in BERT-style models.
- **Dimension reduction**: use Matryoshka embeddings to truncate vectors for faster search.
- **Batch embedding**: embed multiple texts in a single API call for efficiency.
- **Caching**: cache embeddings for frequently embedded texts.
- **Fine-tuning**: adapt embedding models to domain-specific data for better retrieval.
