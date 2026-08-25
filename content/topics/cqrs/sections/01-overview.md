# Overview
CQRS separates the model for reading data (query) from the model for writing data (command). Each side has its own data store, optimized for its access pattern: the write side may use a normalized relational DB for consistency, while the read side uses a denormalized cache or search index for fast queries.

This separation enables independent scaling, different storage technologies, and simpler domain models on each side.
