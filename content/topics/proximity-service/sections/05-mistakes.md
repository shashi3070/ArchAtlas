# Common Mistakes
- **Ignoring edge cases**: businesses on cell boundaries may be missed.
- **No distance filter**: returning results from all geohash cells without radius check.
- **Stale business data**: closed businesses still appearing in results.
- **No caching**: every query hits the database.
- **Ignoring privacy**: always get user consent before using location data.
