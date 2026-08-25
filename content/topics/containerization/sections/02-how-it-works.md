# How It Works
1. **Image**: a read-only template built from a Dockerfile; layers are cached and shared.
2. **Pod**: the smallest deployable unit; one or more co-located containers sharing network and storage.
3. **Deployment**: declares desired replicas and update strategy; the controller creates ReplicaSets.
4. **Service**: ClusterIP (internal), NodePort (external via node), LoadBalancer (cloud LB).
5. **Ingress**: HTTP routing rules (host, path) to Services; TLS termination.
6. **HPA**: Horizontal Pod Autoscaler scales replicas based on CPU, memory, or custom metrics.
