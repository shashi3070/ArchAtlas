# Overview
A bloom filter is a bit array of `m` bits combined with `k` independent hash functions. To add an element, hash it with each function and set the corresponding bits to 1. To query, check if all corresponding bits are 1: if any is 0, the element is definitely not in the set; if all are 1, the element is probably in the set.

Bloom filters use ~10 bits per element for a 1% false positive rate, making them far more space-efficient than hash sets.
