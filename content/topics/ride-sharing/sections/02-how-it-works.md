# How It Works
1. **Location update**: driver app sends GPS coordinates every 4 seconds → location service.
2. **Geospatial index**: location service updates driver's geohash in a spatial index (Redis or Quadtree).
3. **Rider requests ride**: location service queries nearby drivers within a radius.
4. **ETA computation**: pre-computed road graph + current traffic → ETA for each nearby driver.
5. **Dispatch**: match rider to optimal driver (lowest ETA or highest driver rating).
6. **Trip tracking**: real-time GPS updates from both rider and driver → map view.

Components: location service, geospatial index, ETA service, dispatch service, trip service, payment service.
