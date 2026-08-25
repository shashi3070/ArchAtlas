# Overview
In microservice architectures, service instances are ephemeral: they scale up during peaks, roll during deploys, and die during failures. Service discovery solves the problem of locating healthy instances without hardcoding addresses.

Two models exist: client-side (caller queries the registry) and server-side (a load balancer queries the registry and routes traffic). Both require a registry (Consul, etcd, ZooKeeper, or DNS) and health checking.
