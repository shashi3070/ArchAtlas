# Common Mistakes
- **No health check during rolling deploy**: new instances receive traffic before they're ready.
- **Forgetting database migrations**: new code expects schema that doesn't exist yet.
- **Canary without metrics**: deploying to 5% without monitoring is just hope.
- **Feature flag leak**: flags left enabled indefinitely create dead code paths.
- **Blue-green with shared state**: both environments writing to the same database defeats the isolation.
