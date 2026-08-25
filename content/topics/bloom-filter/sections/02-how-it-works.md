# How It Works
1. Initialize a bit array of `m` bits, all zeros.
2. **Insert(x)**: for i in 1..k, set `bits[hash_i(x) % m] = 1`.
3. **Query(x)**: for i in 1..k, if `bits[hash_i(x) % m] == 0`, return 'definitely not'. If all are 1, return 'probably'.
4. **Optimal k**: `k = (m/n) * ln(2)` where n is expected element count.
5. **Optimal m**: `m = -n * ln(p) / (ln(2))^2` where p is target false positive rate.

No deletion support in standard bloom filters; counting bloom filters allow deletion at 4x memory cost.
