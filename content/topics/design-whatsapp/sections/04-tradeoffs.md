# Tradeoffs
**Erlang vs Go/Java**: Erlang's actor model is ideal for connections; Go/Java are more mainstream.
**XMPP vs custom**: XMPP is battle-tested; custom is simpler but requires protocol design.
**Encryption vs features**: E2E encryption prevents server-side search and analytics.

**When to prefer XMPP**: need for federation and interop.
**When to prefer custom protocol**: need for specific optimizations.
