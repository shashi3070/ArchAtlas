# Common Mistakes
- **Single counter**: millions of concurrent increments cause contention.
- **No merge strategy**: regional counters never aggregated to global.
- **Ignoring negative values**: likes should only increase; bugs can cause decrements.
- **No persistence**: Redis loses data on restart; periodic DB snapshots are essential.
- **Polling for count**: real-time count updates should push to connected users.
