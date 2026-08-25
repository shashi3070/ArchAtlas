# Common Mistakes
- **Too few virtual nodes**: with 10 vnodes on 5 nodes, std-dev of load can exceed 30%.
- **Ignoring hot keys**: consistent hashing distributes keys uniformly but not access volume; a single viral key still overloads its owner.
- **Using a non-uniform hash**: modulo with a bad hash function creates persistent skew.
- **Forgetting replication**: single point of failure if each key maps to exactly one node.
