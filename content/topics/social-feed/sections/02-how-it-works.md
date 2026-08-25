# How It Works
**Fan-out-on-write**:
1. User posts → write to their timeline + fan-out to all followers' feed lists.
2. Follower opens feed → read pre-computed feed list → fast.

**Fan-out-on-read**:
1. User posts → write to their timeline only.
2. Follower opens feed → fetch recent posts from all followed accounts → merge and rank → slow.

**Hybrid (Twitter's approach)**:
1. Regular users: fan-out-on-write (fast read).
2. Celebrity users: fan-out-on-read (avoid write amplification).
3. At read time, merge pre-computed feed with live celebrity posts.
