# Overview
Every interactive system starts with a client asking a server for something over HTTP. Before we can reason about load balancers, caches or queues, we need a precise picture of what happens on that journey: a name is resolved (DNS), a connection is opened (TCP), it is secured (TLS), an HTTP message is exchanged, and only then does application logic run.

Three ideas recur throughout this course:

- **Latency budget**: users perceive anything under ~100 ms as instant. Every hop you add spends part of that budget.
- **Statelessness**: HTTP itself is stateless; session state has to live somewhere explicit (cookies, tokens, server stores).
- **Semantics**: verbs (GET/POST/PUT/DELETE) and status codes form a contract. Misusing them confuses caches, proxies and clients alike.
