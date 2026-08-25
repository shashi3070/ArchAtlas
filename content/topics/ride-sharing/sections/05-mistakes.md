# Common Mistakes
- **Polling instead of push**: driver location via polling wastes bandwidth; use persistent connections.
- **No stale driver removal**: drivers who close the app remain in the index.
- **Ignoring GPS accuracy**: GPS can be off by 10-50m; don't assume sub-meter precision.
- **Single-region dispatch**: cross-region matches are slower; partition by geography.
- **No surge pricing**: during peak demand, all drivers are booked; price signals balance supply.
