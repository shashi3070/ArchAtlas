# How It Works
1. Client sends `GET /chat` with `Upgrade: websocket` and `Sec-WebSocket-Key`.
2. Server responds `101 Switching Protocols` with `Sec-WebSocket-Accept`.
3. TCP connection stays open; both sides send binary or text frames.
4. Ping/pong frames detect liveness (typically every 30s).
5. Either side closes with a close frame; TCP teardown follows.

Frame format: FIN bit + opcode (text/binary/ping/pong/close) + mask bit + payload length (1-8 bytes) + optional masking key + payload.
