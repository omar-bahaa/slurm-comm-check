# Communication Check Loop

## Goal

Identify node-level, pair-level, and scale-dependent communication health issues
on the MI210 cluster. Qwen/Megatron hangs and slowdowns motivated the work, but
the benchmark's direct goal is to classify the communication health of nodes and
node groups.

## Working Hypotheses

1. Some nodes have unhealthy ROCm, GPU, NIC, or Slurm/PAM state even when they can
   be allocated.
2. Some node pairs have poor RoCE/NCCL connectivity, causing a small run to pass
   while larger jobs stall when that pair is included.
3. 16-node jobs may fail only when communicator setup or cross-node collectives
   stress all GPU lanes, not when a simple single-rank-per-node test is used.
4. Megatron uses several communication patterns, so a useful benchmark must cover
   global collectives, data-parallel-like same-local-rank collectives, and
   point-to-point neighbor transfers used by pipeline parallelism.

## Benchmark Design

The benchmark in `comm_benchmark.py` runs with `torchrun` and the NCCL backend on
all GPUs of every allocated node. It records:

1. Per-node software health before distributed launch:
   - hostname
   - `/opt/rocm-7.0.0` existence
   - `rocm-smi` availability and output
   - Python, torch, HIP, and visible device information
2. Connection/setup timing:
   - torch import time
   - `init_process_group` wall time
   - first distributed barrier time
3. Global collectives across all ranks:
   - barrier
   - all-reduce
   - all-gather
   - reduce-scatter
   - broadcast
4. Megatron-relevant subgroup collectives:
   - node-local groups of 8 ranks, approximating tensor-parallel intra-node use
   - same-local-rank groups across nodes, approximating data-parallel traffic
5. Pipeline-parallel-like point-to-point:
   - ring `batch_isend_irecv`
   - adjacent even/odd pair `batch_isend_irecv`
6. Per-host summaries:
   - slowest ranks
   - max/mean/p50/p95 latencies
   - bandwidth estimates where message size permits

Each Slurm run writes a self-contained directory under `runs/<job_id>/`
with `allocated_nodes.txt`, per-node health logs, per-node torch logs,
`comm_metrics.json`, and `summary.txt`.

## Slurm Entry Point

Use `run_comm_check.sbatch`. It defaults to 2 nodes and can be overridden:

```bash
sbatch --nodes=4 \
  --export=ALL,EXPECTED_NUM_NODES=4 \
  run_comm_check.sbatch
```

For a fixed node set:

```bash
sbatch --nodes=2 \
  --nodelist=auh7-1b-gpu-[257-258] \
  --export=ALL,EXPECTED_NUM_NODES=2,RUN_LABEL=pair_257_258 \
  run_comm_check.sbatch
```

## Execution Loop

1. Validate the sbatch on any 2 nodes.
2. Inspect `summary.txt`, `comm_metrics.json`, and node logs.
3. Build a 16-node communication test set beginning with excluded/suspect nodes:
   `190,213,215,224,225,226,228,256,265,275,276,280,281,282,287`, plus one
   additional available node if needed.
4. Run 2-node checks in disjoint pairs first.
5. Mark a pair healthy if:
   - ROCm checks pass on both nodes
   - process-group initialization completes
   - global all-reduce, same-local-rank all-reduce, and p2p tests complete
   - no collective has repeated multi-second latency for small tensors
6. If a pair is healthy, do not retest either node with another partner unless a
   later 4/8/16-node run implicates it.
7. If a pair is slow or fails, add the node/pair evidence to `2nodes_faulty.md`
   and cross-check each suspect with a known-good node.
8. After 2-node screening, run 4-node checks on suspect-containing groups and
   then 8-node checks.
9. Run a 16-node check with the current best communication set. If 16 nodes fail but
   all smaller sets pass, inspect:
   - `init_process_group_seconds`
   - same-local-rank cross-node all-reduce by local rank
   - rank-neighbor p2p failures
   - per-node health logs
10. Keep `SUBMITTED_JOBS.md` updated after every `sbatch` and after every result
    inspection.

## Result Files

- `SUBMITTED_JOBS.md`: submitted jobs, node sets, state, and observed result.
- `2nodes_faulty.md`: node or pair evidence from 2-node tests.
- `global_node_summary.md`: per-node roll-up of partners tested, category, and
  supporting speed or error evidence.
- `summary_2nodes.md`, `summary_4nodes.md`, `summary_8nodes.md`,
  `summary_16nodes.md`: scale-specific conclusions and links to run IDs.

## Current Status

Benchmark harness is implemented and validated.

Completed:

- 2-node validation and screening.
- 4-node healthy and degraded comparison.
- 8-node best-current baseline.
- Additional 2-node screening on previously untested nodes.
- One 16-node degraded stress run that completed without a hard RCCL fatal.

Findings:

- Confirmed RCCL/RoCE-fatal nodes: `275`, `276`, `282`, `319`.
- Confirmed distributed-communication suspect with a different failure mode:
  `206` reproducibly fails with `torch.AcceleratorError: HIP error: invalid
  argument` after basic ROCm health passes.
- Degraded pairs: `196/197`, `225/226`, `228/273`, `271/272`, `274/317`,
  `284/285`.
- `287` passes NCCL/RCCL communication with `270`; its earlier failure is likely
  separate SSH/PAM orchestration behavior.
- `200` and `320` passed cross-checks with known-good nodes after failures with
  `206` and `319`, respectively.
- Job `76597` completed on 16 nodes after excluding known RCCL-fatal nodes, but
  it was very slow because it still included degraded pairs.

Next action:

- Continue 2-node coverage on untested nodes to find enough clean nodes for a
  16-node communication-healthy run.
- Retry a 16-node run excluding `206`, `275`, `276`, `282`, and `319`, and avoid
  degraded pairs when enough full nodes are idle.
