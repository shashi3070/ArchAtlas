# Tradeoffs
| Choice | Gains | Costs |
| --- | --- | --- |
| Synchronous request/response | Simple reasoning, immediate result | Caller blocked; failures propagate |
| Async job + polling/push | Resilient to spikes; caller freed | Eventual consistency; more moving parts |
| REST | Ubiquitous tooling, cacheability | Verbose payloads; N+1 fetching |
| gRPC | Compact, typed, streaming | Browser friction; harder debugging |

There is no globally correct answer - the design skill is matching style to operation: reads of user-visible data stay synchronous and cacheable; side effects that take seconds go async; internal calls optimize for efficiency and type safety.
