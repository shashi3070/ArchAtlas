# Patterns
- **PagedAttention**: virtual memory for KV cache; eliminates memory fragmentation (vLLM).
- **Continuous batching**: add/remove requests from the batch dynamically.
- **Speculative decoding**: draft-then-verify for 2-3x speedup.
- **Quantization**: INT8/INT4 reduces memory and increases throughput with slight quality loss.
- **Tensor parallelism**: split model across multiple GPUs.
- **Prefix caching**: cache KV for common system prompts across requests.
