# How It Works
1. **Connection**: client connects via persistent TCP/XMPP connection to a chat server.
2. **Authentication**: mutual TLS + phone number verification.
3. **Message flow**: sender → chat server → message bus → recipient's chat server → recipient.
4. **Offline handling**: messages queued in a distributed queue (Mnesia/Ejabberd) until user reconnects.
5. **Group messaging**: fan-out message to all group members' servers.
6. **Media**: upload to media server → get a CDN URL → share URL in message.

Architecture: Erlang-based chat servers (soft real-time), Mnesia for state, MySQL for message history.
