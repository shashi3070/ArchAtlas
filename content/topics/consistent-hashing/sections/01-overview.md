# Overview
Consistent hashing maps both keys and nodes onto a logical ring identified by hash values. Each key is served by the first node encountered walking clockwise. When a node joins or leaves, only the keys in the affected arc move, unlike modulo hashing which reshuffles everything.

This property makes consistent hashing the default choice for distributed caches, partitioned databases, and content-delivery networks where cluster membership changes without downtime.
