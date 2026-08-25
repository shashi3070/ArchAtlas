# How It Works
1. **Upload**: client uploads raw video to an upload server; video is stored in object storage (S3).
2. **Transcoding**: message queue triggers a transcoding worker; video is encoded into multiple resolutions (360p-4K) and codecs (H.264, H.265).
3. **Packaging**: transcoded segments are packaged into HLS/DASH manifests.
4. **CDN**: segments are pushed to CDN edge nodes; popular content is cached aggressively.
5. **Playback**: player fetches manifest, selects quality variant based on bandwidth, fetches segments.
6. **Recommendations**: ML model generates 'next video' suggestions based on watch history.

Components: upload server, object storage, transcoding workers, CDN, manifest server, recommendation engine.
