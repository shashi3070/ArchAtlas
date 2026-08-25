# Common Mistakes
- **No fallback**: circuit opens and users see raw errors.
- **Too aggressive threshold**: trips on a single transient error.
- **Too long timeout**: dependency is down for minutes before circuit opens.
- **No monitoring**: circuit state changes are invisible; issues go unnoticed.
- **Shared circuit for all dependencies**: one failing dependency opens the circuit for healthy ones.
