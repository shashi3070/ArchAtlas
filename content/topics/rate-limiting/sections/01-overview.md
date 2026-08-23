# Overview
Rate limiting caps how much work a client (or tenant, or the world) may demand per time window. Motives stack: protect finite capacity, isolate noisy neighbors, monetize quotas, blunt abuse. Limits apply at several rings: edge (per-IP/session, coarse), gateway (per-API-key, contractual), service (per-dependency self-protection), and datastore (concurrency caps).

Algorithms trade smoothness for bookkeeping: fixed windows are trivial but allow 2x bursts at boundaries; sliding windows/logs smooth that; token buckets permit controlled bursts; leaky buckets pace output. Distributed enforcement shares state via Redis or gateway-side aggregation - accuracy vs latency overhead is a dial.
