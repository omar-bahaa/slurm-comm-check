# 2-Node Communication Summary

## Job 76325: auh7-1b-gpu-275, auh7-1b-gpu-276

This pair is unhealthy. Both nodes pass basic ROCm checks, but the first torch
distributed validation produced RCCL `NET/IB` fatal-completion warnings on
`rocep97s0f0` from both sides of the connection. The job was canceled after the
failure evidence was captured.

The run also revealed a harness issue: comma-separated size lists must not be
passed inside `srun --export=...`, because Slurm splits that argument on commas.
`run_comm_check.sbatch` now exports variables in the shell and uses
`srun --export=ALL`.

## Job 76327: auh7-1b-gpu-267, auh7-1b-gpu-268

This pair is healthy and validates the benchmark harness end to end.

- State: completed in 25 seconds.
- Run directory: `runs/76327_validation_267_268`
- Output files: `comm_metrics.json`, `summary.txt`, per-node health logs, and
  per-node torchrun logs.
- ROCm software health: passed on both nodes.
- No metric crossed the built-in suspicious thresholds.
- Representative timings:
  - world all-reduce 1 MiB: p95 about 0.58 ms.
  - world all-reduce 64 MiB: p95 about 13.27 ms.
  - same-local-rank cross-node all-reduce 16 MiB: p95 about 3.5-3.6 ms across
    local ranks.
  - ring p2p 64 MiB: p95 about 31.9 ms.

## Jobs 76331 and 76332: 275/276 Cross-Checks

The failed `275`/`276` pair was split across known-good baseline nodes:

- `76331`: `267` with `275`
- `76332`: `268` with `276`

Both cross-checks reproduced the RCCL `NET/IB` `status=12` / `vendor err 10`
failure on `rocep97s0f0`. This isolates `275` and `276` as individually bad for
NCCL/RCCL communication, because `267` and `268` completed the same benchmark
together in job `76327`.

## Additional 2-Node Screening

| Job | Pair | Classification | Key Evidence |
|---|---|---|---|
| `76333` | `269,270` | Healthy | all-reduce 1 MiB p95 0.58 ms; 64 MiB p95 12.89 ms |
| `76334` | `271,272` | Degraded | all-reduce 1 MiB p95 3.05 ms; 64 MiB p95 54.81 ms; ring p2p 64 MiB p95 78.90 ms |
| `76335` | `282,287` | Failed | RCCL `NET/IB` status=12/vendor err 10 |
| `76336` | `284,285` | Severely degraded | all-reduce 1 MiB p95 19.96 ms; 64 MiB p95 93.00 ms; same-local-rank 1 MiB all-reduce up to 24.11 ms |
| `76337` | `286,296` | Mostly healthy | all-reduce 1 MiB p95 0.64 ms; 64 MiB p95 24.14 ms |
| `76338` | `297,227` | Mostly healthy | all-reduce 1 MiB p95 0.65 ms; 64 MiB p95 23.65 ms |
| `76340` | `269,282` | Failed | `282` reproduced RCCL `NET/IB` failure with healthy `269` |
| `76341` | `270,287` | Healthy for communication | `287` completed with healthy `270`; earlier issue on `287` is likely SSH/PAM orchestration-specific |
| `76349` | `210,224` | Usable | all-reduce 1 MiB p95 0.62 ms; 64 MiB p95 13.42 ms |
| `76350` | `225,226` | Degraded | all-reduce 1 MiB p95 3.44 ms; 64 MiB p95 54.74 ms; ring p2p 64 MiB p95 78.99 ms |
| `76351` | `240,252` | Usable | all-reduce 1 MiB p95 0.61 ms; 64 MiB p95 13.55 ms |
| `76592` | `196,197` | Degraded | all-reduce 1 MiB p95 3.37 ms; 64 MiB p95 54.78 ms; ring p2p 64 MiB p95 79.00 ms |
| `76593` | `200,206` | Failed | `206` ranks failed with `torch.AcceleratorError: HIP error: invalid argument`; no metrics |
| `76594` | `228,273` | Severely degraded | all-reduce 1 MiB p95 24.82 ms; 64 MiB p95 92.93 ms; same-local-rank 1 MiB all-reduce about 19.75-19.81 ms |
| `76595` | `274,317` | Degraded | all-reduce 1 MiB p95 3.40 ms; 64 MiB p95 58.89 ms; ring p2p 64 MiB p95 78.73 ms |
| `76596` | `319,320` | Failed | RCCL `NET/IB` status=12/vendor err 10; later isolated to `319` |
| `76599` | `200,267` | Usable | `200` passed with known-good `267`; all-reduce 1 MiB p95 0.683 ms; 64 MiB p95 25.41 ms |
| `76600` | `206,268` | Failed | `206` reproduced `torch.AcceleratorError: HIP error: invalid argument` with known-good `268` |
| `76601` | `319,269` | Failed | `319` reproduced RCCL `NET/IB` status=12/vendor err 10 with known-good `269` |
| `76602` | `320,270` | Usable | `320` passed with known-good `270`; all-reduce 1 MiB p95 0.672 ms; 64 MiB p95 25.66 ms |

Current bad-for-communication nodes from 2-node evidence: `206`, `275`, `276`,
`282`, `319`.

Current degraded pairs that should not be classified as healthy communication
paths without more isolation: `196/197`, `225/226`, `228/273`, `271/272`,
`274/317`, `284/285`.

Nodes cleared by cross-checks in this batch:

- `200` passed with known-good `267` after the original `200/206` failure.
- `320` passed with known-good `270` after the original `319/320` failure.
