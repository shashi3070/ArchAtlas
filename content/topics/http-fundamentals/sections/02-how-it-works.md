# How It Works
A request to `https://api.example.com/items` proceeds roughly as follows:

1. **DNS resolution** - the hostname maps to an IP (possibly a load balancer). TTLs control how long resolvers may cache the answer.
2. **TCP handshake** - one round trip (SYN, SYN-ACK, ACK). Over TLS 1.3, key exchange adds one more round trip before application bytes flow.
3. **HTTP exchange** - the client sends method, path, headers and optional body; the server returns a status code, headers and body.
4. **Connection reuse** - keep-alive lets subsequent requests skip steps 2-3 setup; HTTP/2 multiplexes many streams over one connection.

Round trips dominate. A service that needs four sequential downstream calls pays at least four times their latency, which is why fan-out patterns and parallelism appear again and again in system design.
