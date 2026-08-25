# Overview
A chat system provides real-time 1:1 and group messaging with delivery guarantees, message ordering, presence indicators, and media sharing. The core challenges are connection management, message routing, and offline handling.

WhatsApp serves 100B+ messages/day with 32 engineers by making smart architectural choices: XMPP protocol, Erlang for concurrency, and a distributed message queue for routing.
