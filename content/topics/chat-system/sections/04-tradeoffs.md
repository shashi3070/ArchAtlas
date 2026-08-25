# Tradeoffs
**Fan-out on write**: fast reads (inbox pre-computed); expensive for large groups; write amplification.
**Fan-out on read**: cheap writes; expensive reads for active users; good for broadcast channels.
**XMPP vs custom**: XMPP is battle-tested but complex; custom is simpler but requires protocol design.

**When to prefer fan-out on write**: small groups (<100 members); high read-to-write ratio.
**When to prefer fan-out on read**: large groups/broadcast channels; write-to-read ratio is high.
