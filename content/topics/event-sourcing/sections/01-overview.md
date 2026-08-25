# Overview
Event sourcing stores every state change as an immutable event in an append-only log. The current state is derived by replaying events. This provides a complete audit trail, enables temporal queries (state at time T), and supports building multiple read models from the same event stream.

Event sourcing is not a database technology; it's an architectural pattern that pairs well with CQRS.
