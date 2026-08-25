# Common Mistakes
- **No KV cache**: recomputing attention for every token is 10x slower.
- **Over-provisioning GPUs**: idle GPUs are expensive; use autoscaling.
- **Ignoring cold start**: model loading takes minutes; keep warm instances.
- **No request queuing**: without a queue, requests are dropped during spikes.
- **Ignoring cost**: LLM inference costs can spiral; monitor cost per request.
