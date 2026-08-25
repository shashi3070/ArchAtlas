# Overview
Idempotency means a request can be applied multiple times without changing the result beyond the first application. In distributed systems, network retries, message queue redelivery, and load balancer failovers all cause duplicate requests.

Idempotency is essential for financial operations (payments, transfers), resource creation (orders, accounts), and any operation where duplication causes visible harm.
