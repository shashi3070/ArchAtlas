# How It Works
1. **Tokenization**: input text is tokenized into token IDs.
2. **Prefill**: all input tokens are processed in parallel (compute-bound).
3. **Decode**: output tokens are generated one at a time (memory-bandwidth-bound).
4. **KV cache**: key-value tensors from attention layers are cached across decode steps.
5. **Sampling**: logits are sampled (greedy, top-k, top-p) to select the next token.
6. **Stop condition**: max tokens reached or stop token generated.

Infrastructure: vLLM, TensorRT-LLM, TGI (HuggingFace), Triton Inference Server.
