# Overview
A social media feed aggregates posts from accounts a user follows into a personalized, ranked timeline. The two dominant approaches are fan-out-on-write (pre-compute feeds) and fan-out-on-read (compute at read time).

Twitter uses a hybrid: fan-out-on-write for regular users, fan-out-on-read for celebrities, combining the strengths of both.
