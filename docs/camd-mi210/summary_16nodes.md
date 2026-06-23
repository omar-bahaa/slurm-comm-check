# 16-Node Communication Summary

## Attempted Jobs

### Job 76354

- Intended nodes: `210,224-227,240,252,267-271,286-287,296-297`
- State: canceled before running.
- Reason: pending on resources after `224-226` were allocated by other work.
- Result: no benchmark data.

### Job 76361

- Intended nodes: `227,240,252,267-272,282,284-287,296-297`
- State: canceled before running.
- Reason: pending on resources after required nodes became `mixed-`.
- Result: no benchmark data.
- Note: this was not a clean 16-node communication set because it included known
  RCCL-bad `282`; it was only submitted because fewer than 16 non-bad idle nodes
  were available.

### Job 76597

- Nodes: `196`, `197`, `227`, `228`, `267`, `268`, `269`, `270`, `271`, `272`,
  `273`, `274`, `286`, `296`, `297`, `317`
- State: completed.
- Run directory: `runs/76597_16node_degraded_no_fatal_known`
- Result: no hard RCCL fatal, but the run is not communication-healthy.
- ROCm software health: passed on all 16 nodes.
- Representative timings:
  - world all-reduce 1 MiB: p95 40.01 ms, max 40.31 ms.
  - world all-reduce 64 MiB: p95 56.91 ms.
  - same-local-rank cross-node all-reduce 1 MiB: p95 about 40.8 ms across
    local ranks.
  - same-local-rank cross-node all-reduce 16 MiB: local rank 4 p95 104.76 ms,
    local ranks 6 and 7 p95 about 58.3-58.4 ms.
  - ring p2p 64 MiB: p95 79.29 ms.
- Interpretation: excluding known RCCL-fatal nodes is enough to avoid a hard
  hang in this run, but degraded links still dominate the 16-node collective
  path. This node set is useful as a communication stress datapoint, not as a
  clean communication baseline.

## Current 16-Node Readiness

A clean 16-node communication-healthy benchmark has not run yet. Job `76597`
completed, but it intentionally included degraded pairs because enough clean
exclusive nodes were not available. The next 16-node attempt should exclude
confirmed bad nodes:

- `auh7-1b-gpu-206`
- `auh7-1b-gpu-275`
- `auh7-1b-gpu-276`
- `auh7-1b-gpu-282`
- `auh7-1b-gpu-319`

It should also avoid degraded pairs if enough alternatives are available:

- `auh7-1b-gpu-[196-197]`
- `auh7-1b-gpu-[225-226]`
- `auh7-1b-gpu-228` with `auh7-1b-gpu-273`
- `auh7-1b-gpu-[271-272]`
- `auh7-1b-gpu-274` with `auh7-1b-gpu-317`
- `auh7-1b-gpu-[284-285]`

The best currently screened pool for a future clean communication attempt is:

- usable/healthy: `210`, `224`, `227`, `240`, `252`, `267`, `268`, `269`,
  `270`, `286`, `287`, `296`, `297`, `200`, `320`
- usable but less screened or degraded if needed: `196`, `197`, `225`, `226`,
  `228`, `271`, `272`, `273`, `274`, `317`

If at least 16 full nodes are available, run:

```bash
sbatch --nodes=16 \
  --exclude=auh7-1b-gpu-206,auh7-1b-gpu-275,auh7-1b-gpu-276,auh7-1b-gpu-282,auh7-1b-gpu-319 \
  --export=ALL,EXPECTED_NUM_NODES=16,RUN_LABEL=16node_clean_retry,COMM_MEASURE_ITERS=2,COMM_WARMUP_ITERS=1 \
  run_comm_check.sbatch
```
