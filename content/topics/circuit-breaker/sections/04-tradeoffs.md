# Tradeoffs
**Pros**: Prevents cascade failures; fast failure improves user experience; protects failing dependencies from overload.
**Cons**: Adds complexity; may mask underlying issues if fallbacks are too generous; half-open trial requests may still fail.

**When to skip**: synchronous calls within a single process (use local error handling); very low call volume where failures are rare enough to not matter.
