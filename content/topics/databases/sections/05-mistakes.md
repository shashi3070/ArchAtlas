# Mistakes
- **N+1 queries** - ORM loops issuing one query per row; batch with IN clauses or join fetch.
- **Missing composite index for sort+filter** - separate single-column indexes rarely combine efficiently.
- **Long transactions holding locks** - keep them short; move external calls out of transaction scope.
- **SELECT \*** over wide tables** - drags TOAST/large columns through buffers; select needed columns.
- **Skipping connection pooling** - thousands of direct connections exhaust memory; pool at app side (PgBouncer server-side).
