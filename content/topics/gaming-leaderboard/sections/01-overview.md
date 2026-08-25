# Overview
A gaming leaderboard ranks players by score in real-time. The system must handle millions of score updates per second while serving rank queries in sub-10ms latency.

Redis sorted sets are the standard solution: O(log N) insert and rank queries, with O(1) score lookups.
