# Overview
A saga is a sequence of local transactions where each step publishes an event that triggers the next. If a step fails, previously completed steps are compensated (reversed) through dedicated compensating transactions.

Sagas replace distributed 2PC (two-phase commit) in microservice architectures, trading strong consistency for availability and partition tolerance.
