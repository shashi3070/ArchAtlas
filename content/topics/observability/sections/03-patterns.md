# Patterns
- **Golden signals dashboards** per service: traffic, errors, latency, saturation - the first screen during incidents.
- **Exemplars**: link metric spikes to example traces for one-click drilling.
- **Structured logging with levels that mean things**: ERROR = needs action; WARN = degraded; INFO = business milestones.
- **Synthetic checks**: proactively exercise critical flows (login, checkout) from outside; catch regional breakage before users report.
- **Postmortem loop**: blameless reviews feed concrete instrumentation/backpressure fixes; repeat incidents signal unfinished fixes.
