# Patterns
- **Sidecar**: inject logging, monitoring, or proxy containers into every pod (service mesh pattern).
- **Init containers**: run setup tasks (migrations, waiting for dependencies) before the main container starts.
- **Liveness/readiness probes**: liveness restarts stuck containers; readiness gates traffic to ready pods.
- **Resource requests/limits**: requests ensure scheduling; limits prevent noisy neighbours.
- **Pod Disruption Budgets**: guarantee minimum availability during voluntary disruptions (node drains).
- **GitOps**: declarative infrastructure via Git; ArgoCD or Flux reconciles cluster state to Git.
