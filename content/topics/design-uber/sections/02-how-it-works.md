# How It Works
1. **Driver location**: GPS updates every 4 seconds → location service → geospatial index.
2. **Rider request**: user requests ride → location service queries nearby drivers.
3. **ETA computation**: pre-computed road graph + traffic → ETA for each driver.
4. **Dispatch**: match rider to optimal driver (lowest ETA, highest rating).
5. **Trip**: real-time GPS tracking → map view for rider and driver.
6. **Payment**: fare calculated from distance + time + surge multiplier.

Architecture: Ringpop (gossip protocol), Trips (trip management), Dispatcher (matching), S2 (geospatial library).
