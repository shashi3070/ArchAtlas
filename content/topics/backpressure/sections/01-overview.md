# Overview
Backpressure is the feedback mechanism that prevents a fast producer from overwhelming a slow consumer. Without it, buffers grow unbounded, memory is exhausted, and the system crashes.

Backpressure appears at every layer: TCP windowing, request queuing, stream processing (Kafka consumer lag), and database connection pooling. The key design choice is the overflow strategy: block, drop, or shed load.
