# 8-Node Communication Summary

## Job 76346: Best Current 8-Node Set

- Nodes: `auh7-1b-gpu-[227,267-270,286,296-297]`
- State: completed.
- ROCm health: passed on all nodes.
- Result: healthy 8-node scale check.
- Key metrics:
  - world all-reduce 1 MiB: p95 1.05 ms.
  - world all-reduce 64 MiB: p95 35.32 ms.
  - ring p2p 64 MiB: p95 35.26 ms.
  - same-local-rank cross-node all-reduce 1 MiB: p95 about 1.2-1.34 ms.
  - same-local-rank cross-node all-reduce 16 MiB: p95 about 7.9-10.95 ms.

Conclusion: this 8-node set is suitable as the current clean baseline for
larger tests. The only suspicious entries were setup/first-barrier timing on
some ranks, not sustained collective bandwidth.
