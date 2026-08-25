# Tradeoffs
**Choreography**: simple, no SPOF, loosely coupled; hard to debug, order is implicit, hard to add new steps.
**Orchestration**: explicit flow, easy to add steps, centralized error handling; SPOF, tight coupling to orchestrator.

**Sagas vs. 2PC**: sagas are available and partition-tolerant; 2PC provides stronger consistency but blocks on failures.

**When to prefer 2PC**: financial systems requiring strict consistency; small number of participants; acceptable latency.
