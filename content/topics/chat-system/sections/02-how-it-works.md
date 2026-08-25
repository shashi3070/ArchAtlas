# How It Works
1. Client connects via WebSocket to a chat server; maintains a persistent connection.
2. Chat server authenticates the user and maps user_id → server_id in a presence service.
3. Sender sends message → chat server assigns sequence ID → publishes to message bus.
4. Recipient's chat server subscribes to the bus → pushes message via WebSocket.
5. If recipient is offline → store in offline queue (DB or Redis list).
6. Group chat: fan-out message to all group members' servers via the bus.

Components: WebSocket gateway, chat server, presence service, message bus, message store, media service.
