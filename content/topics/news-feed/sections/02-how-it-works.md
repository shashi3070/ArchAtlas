# How It Works
1. User creates a post → write to their timeline + fan-out to followers' feeds.
2. Follower opens feed → read pre-computed feed list.
3. Feed ranking: ML model scores each post by predicted engagement.
4. Real-time updates: new posts from followed accounts appear at the top.
5. Pagination: cursor-based; load more posts on scroll.

Feed computation: fan-out-on-write for regular users; fan-out-on-read for celebrity accounts.
Ranking: gradient-boosted trees predicting like/comment/share probability.
