# Overview
A proximity service finds nearby businesses, restaurants, or points of interest based on a user's location. The system must handle millions of location queries per second with sub-100ms latency.

The core challenge is efficiently querying a 2D spatial index that supports radius and bounding-box queries.
