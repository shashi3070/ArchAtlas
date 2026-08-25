# How It Works
1. **Upload**: chunked upload with resumability; stored in object storage (GCS/S3).
2. **Transcoding**: parallel workers encode into multiple resolutions and codecs.
3. **Packaging**: HLS/DASH manifests created for adaptive streaming.
4. **CDN**: segments pushed to CDN edge nodes; tiered caching.
5. **Playback**: player fetches manifest, selects quality, fetches segments.
6. **Recommendations**: ML model generates personalized suggestions.
7. **Monetization**: ad insertion (pre-roll, mid-roll) based on viewer demographics.
