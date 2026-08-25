# How It Works
1. **Nouns, not verbs**: `GET /orders/{id}` not `GET /getOrder?id=1`.
2. **HTTP methods**: GET (read), POST (create), PUT (replace), PATCH (partial update), DELETE (remove).
3. **Status codes**: 200 (OK), 201 (Created), 204 (No Content), 400 (Bad Request), 404 (Not Found), 409 (Conflict), 429 (Rate Limited), 500 (Internal).
4. **Error format**: JSON with error code, message, and details array.
5. **Pagination**: `?cursor=abc123&limit=20` with `Link` header for next/prev.
6. **Idempotency keys**: client-generated UUID in header for POST/PUT to prevent duplicate processing.
