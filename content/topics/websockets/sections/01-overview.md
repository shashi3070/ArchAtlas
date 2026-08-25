# Overview
WebSockets provide a persistent, full-duplex channel between client and server over a single TCP connection. After an HTTP-based handshake, both sides can send frames at any time with minimal overhead (2-14 bytes of framing per message vs. 800+ bytes for HTTP headers).

They are the default choice for chat, multiplayer games, live dashboards, collaborative editing, and any scenario where the server needs to push updates instantly without the client polling.
