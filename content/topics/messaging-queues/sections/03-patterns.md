# Patterns
- **Work queue**: N workers compete on one queue; scale workers with backlog age.
- **Publish/subscribe**: events broadcast to interested services (email, analytics, audit) without producer knowledge.
- **Request/reply over queues**: correlation IDs pair responses to requests for slow RPC-style jobs.
- **Saga/choreography**: long workflows chain events with compensating actions instead of distributed transactions.
- **Priority lanes**: urgent notifications jump ahead of bulk exports via separate queues and dedicated consumers.
