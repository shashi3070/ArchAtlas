# How It Works
Instrument services with **RED** (rate/errors/duration per endpoint) plus **USE** for resources (utilization/saturation/errors per infra node). Emit structured logs (JSON) with correlation ids: request_id, trace_id, tenant. Tracing implementations (OpenTelemetry SDKs) propagate context headers (`traceparent`) across HTTP/gRPC/queue hops; spans record timing and attributes per hop, assembled into watermarks by the backend (Jaeger, Tempo, Datadog).

Alerting discipline: define **SLIs** (measurable service indicators - fraction of requests <300ms), **SLOs** (targets - 99.9% over 28 days), and alert on **burn rate** - consuming error budget too fast pages; slow burn tickets. Everything else routes to dashboards, not phones.
