# 4-Node Communication Summary

## Job 76344: Healthy 4-Node Baseline

- Nodes: `auh7-1b-gpu-[267-270]`
- State: completed.
- ROCm health: passed on all nodes.
- Result: healthy scale-up from 2 nodes.
- Key metrics:
  - world all-reduce 1 MiB: p95 0.77 ms.
  - world all-reduce 64 MiB: p95 23.90 ms.
  - ring p2p 64 MiB: p95 32.20 ms.
  - same-local-rank cross-node all-reduce 1 MiB: p95 about 0.88-1.02 ms
    depending on local rank.

## Job 76345: Degraded 4-Node Group

- Nodes: `auh7-1b-gpu-[271-272,284-285]`
- State: completed, but badly degraded.
- ROCm health: passed on all nodes.
- Result: confirms that the slow 2-node pairs become a severe cross-node
  collective bottleneck at 4 nodes.
- Key metrics:
  - world all-reduce 1 MiB: p95 29.03 ms.
  - world all-reduce 64 MiB: p95 46.09 ms.
  - ring p2p 64 MiB: p95 79.32 ms.
  - same-local-rank cross-node all-reduce 1 MiB: p95 about 31.3 ms for every
    local rank.
  - same-local-rank cross-node all-reduce 16 MiB: p95 about 74.7 ms for every
    local rank.

Conclusion: `267-270` are suitable as a healthy 4-node communication baseline.
The `271/272/284/285` group is a degraded communication group and should be
isolated further before treating any of those nodes as healthy at larger scale.
