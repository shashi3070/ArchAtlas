# Overview
Observability answers questions you didn't pre-script. Three pillars complement each other:

- **Metrics** - numeric time series; cheap, aggregatable, ideal for trends and alerts (Prometheus model).
- **Logs** - discrete events with context; forensic detail, expensive at volume.
- **Traces** - causal chains through request lifetimes; pinpoint which hop added latency or threw.

Cardinality is the budget knob: a label `user_id` on metrics explodes storage and query cost - reserve high-cardinality identifiers for logs/traces, aggregate metrics along bounded dimensions (route, status class, region).
