# Overview
A distributed counter tracks metrics like likes, views, or upvotes across millions of users. The system must handle millions of increments per second with approximate accuracy.

The core challenge is coordinating increments across distributed servers without locks, which would be a bottleneck at scale.
