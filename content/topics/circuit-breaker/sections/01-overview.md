# Overview
The circuit breaker monitors calls to a dependency. When failures exceed a threshold, it trips (opens) and short-circuits subsequent calls, failing fast instead of waiting for timeouts. After a cooldown, it allows a trial request (half-open) to test recovery.

Without circuit breakers, a failing dependency causes callers to pile up on timeouts, exhausting threads and causing cascade failures across the system.
