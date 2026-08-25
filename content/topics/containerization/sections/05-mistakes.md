# Common Mistakes
- **No resource limits**: one pod can starve others on the same node.
- **Missing liveness probes**: stuck containers run forever without restart.
- **Using `latest` tag**: un reproducible deploys; always pin versions.
- **No PodDisruptionBudgets**: cluster upgrades can take down all replicas.
- **Overly complex Helm charts**: simple kustomize or raw YAML is often sufficient.
