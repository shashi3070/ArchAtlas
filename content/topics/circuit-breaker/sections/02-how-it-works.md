# How It Works
1. **Closed** (normal): requests pass through; a failure counter tracks recent failures.
2. If failures exceed the threshold (e.g., 5 failures in 60s) or error rate exceeds 50%, the circuit **opens**.
3. **Open**: all requests fail immediately with a `CircuitBreakerOpenException`.
4. After the timeout (e.g., 30s), the circuit transitions to **half-open**.
5. **Half-open**: one trial request is allowed through.
6. If it succeeds, the circuit **closes** (reset counters). If it fails, the circuit **opens** again.

Libraries: Hystrix (deprecated), Resilience4j, Polly (.NET), pybreaker (Python).
