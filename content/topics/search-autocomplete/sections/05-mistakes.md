# Common Mistakes
- **No caching**: every keystroke hits the trie service.
- **Ignoring typos**: autocomplete should handle fuzzy matching (e.g., 'yotube' → 'youtube').
- **No blacklisting**: offensive or harmful suggestions harm brand.
- **Stale rankings**: suggestions reflect last month's trends, not current.
- **Too many results**: returning 20 suggestions is overwhelming; top 5-8 is optimal.
