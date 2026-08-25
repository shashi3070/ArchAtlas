# Overview
A distributed lock provides mutual exclusion across multiple processes on different machines. Unlike a mutex in a single process, a distributed lock must handle network partitions, process crashes, and clock skew.

Common implementations: Redis (SETNX with TTL), ZooKeeper (ephemeral sequential nodes), etcd (lease-based), and database rows with advisory locks. Each has different consistency and performance characteristics.
