# Tradeoffs
Sticky routing improves cache hit-rate and websocket stability but breaks even spreading when keys skew. Least-connections needs slightly more state and behaves best when request durations vary widely. L4 passthrough is cheap and preserves client IPs trivially, yet cannot route by path or retry intelligently; L7 gives rich control but becomes part of your capacity plan and failure surface.

Also weigh **where** balancing happens: client-side discovery (SDK picks an instance from a registry) removes a central hop and its latency, but pushes rebalancing logic into every language stack. Server-side LBs centralize tuning and observability at the price of an extra network stage and a component that must itself scale.
