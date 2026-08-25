# Overview
LLM inference is the process of generating text from a trained model. Serving LLMs at scale requires managing GPU resources, batching requests, caching intermediate computations, and optimizing for latency vs throughput.

Key challenges: GPU memory is expensive; attention is O(n^2); autoregressive generation is sequential.
