# 2-Node Faulty Communication Evidence

## auh7-1b-gpu-275 <-> auh7-1b-gpu-276

- Job: `76325`
- Run directory: `runs/76325_validation_2node`
- State: canceled after RCCL failure symptoms appeared, to avoid waiting for the
  full timeout.
- ROCm software health:
  - `/opt/rocm-7.0.0` exists on both nodes.
  - `rocm-smi` resolves to `/opt/rocm-7.0.0/bin/rocm-smi` and reports 8 MI210
    GPUs on both nodes.
- Failure evidence:
  - `node0_auh7-1b-gpu-275_torchrun.log` reports RCCL `NET/IB` completion from
    peer `172.27.112.89` with `status=12`, `vendor err 10`, and `local work
    queue catastrophic error` on `rocep97s0f0`.
  - `node1_auh7-1b-gpu-276_torchrun.log` reports matching RCCL `NET/IB`
    send/recv completions from peer `172.27.112.79` with the same status/vendor
    error class.
- Interpretation: software health is not the blocker for this pair. The failure
  is in the RoCE/RCCL path and is consistent with training hangs or peer
  shutdowns observed at larger scale.

## auh7-1b-gpu-275 cross-check

- Job: `76331`
- Pair: `auh7-1b-gpu-267` and `auh7-1b-gpu-275`
- Run directory: `runs/76331_cross_267_275`
- Result: failed/hung after RCCL `NET/IB` fatal-completion warnings.
- Evidence:
  - Healthy baseline `267` completed successfully with `268` in job `76327`.
  - Against `275`, `267` reported peer `172.27.112.79` with `status=12`,
    `vendor err 10`, and `local work queue catastrophic error`.
  - `275` reported matching recv failure from `267`.
- Interpretation: `275` is individually bad on the RCCL/RoCE path, not merely
  bad when paired with `276`.

## auh7-1b-gpu-276 cross-check

- Job: `76332`
- Pair: `auh7-1b-gpu-268` and `auh7-1b-gpu-276`
- Run directory: `runs/76332_cross_268_276`
- Result: failed/hung after RCCL `NET/IB` fatal-completion warnings.
- Evidence:
  - Healthy baseline `268` completed successfully with `267` in job `76327`.
  - Against `276`, `268` reported peer `172.27.112.89` with `status=12`,
    `vendor err 10`, and `local work queue catastrophic error`.
  - `276` reported matching recv failure from `268`.
- Interpretation: `276` is individually bad on the RCCL/RoCE path, not merely
  bad when paired with `275`.

## auh7-1b-gpu-282 cross-check

- Jobs: `76335`, `76340`
- Pairs:
  - `76335`: `auh7-1b-gpu-282` with `auh7-1b-gpu-287`
  - `76340`: `auh7-1b-gpu-282` with healthy `auh7-1b-gpu-269`
- Result: failed/hung after RCCL `NET/IB` fatal-completion warnings.
- Evidence:
  - `76335` showed peer failures between `282` and `287`.
  - `76341` showed `287` completes the same benchmark with healthy `270`.
  - `76340` showed `282` fails against healthy `269` with `status=12`,
    `vendor err 10`, and `local work queue catastrophic error`.
- Interpretation: `282` is individually bad on the RCCL/RoCE path.

## auh7-1b-gpu-206 cross-check

- Jobs: `76593`, `76600`
- Pairs:
  - `76593`: `auh7-1b-gpu-200` with `auh7-1b-gpu-206`
  - `76600`: `auh7-1b-gpu-206` with known-good `auh7-1b-gpu-268`
- Result: failed before benchmark metrics were written.
- ROCm software health:
  - `/opt/rocm-7.0.0` exists on `206`.
  - `rocm-smi` and torch device checks passed in both jobs.
- Evidence:
  - In `76593`, all `206`-side ranks failed during distributed setup/object
    gather with `torch.AcceleratorError: HIP error: invalid argument`.
  - In `76600`, `206` failed the same way against known-good `268`.
  - The peer node in `76600` then reported TCPStore/NCCL setup failures because
    ranks on `206` had already exited.
  - `200` passed a cross-check with known-good `267` in job `76599`, so the
    original `200/206` failure does not implicate `200`.
- Interpretation: `206` is individually suspect for multi-GPU distributed
  communication. This failure mode is not the usual RCCL `NET/IB`
  status=12/vendor err 10 signature, but it is reproducible across partners.

## auh7-1b-gpu-319 cross-check

- Jobs: `76596`, `76601`
- Pairs:
  - `76596`: `auh7-1b-gpu-319` with `auh7-1b-gpu-320`
  - `76601`: `auh7-1b-gpu-319` with known-good `auh7-1b-gpu-269`
- Result: failed/hung after RCCL `NET/IB` fatal-completion warnings.
- ROCm software health:
  - `/opt/rocm-7.0.0` exists on `319`.
  - `rocm-smi` and torch device checks passed before distributed launch.
- Evidence:
  - In `76596`, `320` reported RCCL `NET/IB` completion from peer
    `172.27.112.52` with `status=12`, `vendor err 10`, and `local work queue
    catastrophic error` on `rocep97s0f0`.
  - In `76601`, known-good `269` and `319` reported the same error class when
    paired together.
  - `320` passed a cross-check with known-good `270` in job `76602`, so the
    original `319/320` failure does not implicate `320`.
- Interpretation: `319` is individually bad on the RCCL/RoCE path.
