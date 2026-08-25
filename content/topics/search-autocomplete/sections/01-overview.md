# Overview
Search autocomplete suggests query completions as the user types. The system must handle millions of concurrent users with sub-50ms latency while reflecting current search trends.

The core data structure is a trie (prefix tree) with frequency-weighted ranking, backed by a cache layer for the hottest prefixes.
