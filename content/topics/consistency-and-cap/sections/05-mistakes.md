# Mistakes
- **Reading followers right after writes** - classic "my update disappeared"; implement RYW explicitly.
- **Assuming clocks order events** - wall-clock timestamps lie across nodes; use logical versions for conflict decisions.
- **LWW on collaborative data** - concurrent edits overwrite each other invisibly.
- **Testing only the happy path** - partitions and failovers must be exercised (chaos drills) before production finds them.
- **One model for everything** - blanket 'strongly consistent' or 'eventually consistent' flags ignore per-flow requirements.
