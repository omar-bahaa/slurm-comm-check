# Global Node Communication Summary

This table summarizes every node that produced benchmark data or communication
failure evidence. Jobs that were canceled while still pending in the Slurm queue
are intentionally excluded.

Metric evidence uses p95 latency unless stated otherwise. For healthy or slow
2-node cases, the headline speed is usually world all-reduce. For failed cases,
the evidence is the observed error type. A node marked `Too slow / pair not
isolated` completed communication but only in a slow pair or slow larger group;
that category means the node should not be treated as communication-healthy
until a cross-check isolates whether the node or its partner/link is responsible.

Audit status as of 2026-06-22: this table was checked against every completed
or failed run directory under `runs/` and the matching Slurm logs under `logs/`.
All 32 nodes present in `runs/*/allocated_nodes.txt` are represented below, and
there are no node rows without run evidence. Job `76597` is treated as a
degraded 16-node stress datapoint only; it did not establish a clean 16-node
communication baseline.

## Category Legend

| Category | Meaning | Communication Use |
|---|---|---|
| `Comm failed` | The node reproduced a hard distributed-communication failure, usually with more than one partner or against a known-good partner. Evidence includes RCCL `NET/IB` fatal completions or reproducible HIP/NCCL setup errors after ROCm health passed. | Exclude from multinode communication groups until the node or network path is fixed and retested. |
| `Too slow / pair not isolated` | Communication completed, but latency is far above the healthy baseline. The evidence currently implicates a pair or group, not one specific endpoint. | Do not classify as communication-healthy yet. Retest each node against a known-good partner before deciding whether only one node is bad. |
| `Healthy` | The node completed one or more communication benchmarks with normal collective and p2p latency, including healthy scale checks where available. | Good node for multinode communication groups. |
| `Healthy / usable` | The node completed a 2-node communication benchmark with acceptable latency, but has less scale evidence than the strongest healthy baseline nodes. | Usable for communication groups, especially when more scale-tested healthy nodes are insufficient. Prefer more scale-tested healthy nodes first. |
| `Healthy after cross-check` | The node appeared in a failed pair, but a later cross-check with a known-good partner passed and the failure was isolated to the other node. | Treat as communication-usable. Keep the failed-pair context in mind, but do not exclude based on the earlier failed partner. |
| `Healthy communication; SSH/PAM separate` | NCCL/RCCL communication passed, but this node had a separate non-communication issue in SSH/PAM/Slurm adoption behavior. | Usable for communication if launched through a Slurm-safe path. Keep orchestration issues separate from comm-health classification. |

## Node Table

| Node | Tried With | Category | Evidence |
|---|---|---|---|
| `auh7-1b-gpu-196` | `197`; 16-node set `76597` | Too slow / pair not isolated | With `197`: all-reduce 1 MiB `3.37 ms`, 64 MiB `54.78 ms`, ring p2p 64 MiB `79.00 ms`. In 16-node set: all-reduce 1 MiB `40.01 ms`. |
| `auh7-1b-gpu-197` | `196`; 16-node set `76597` | Too slow / pair not isolated | With `196`: all-reduce 1 MiB `3.37 ms`, 64 MiB `54.78 ms`, ring p2p 64 MiB `79.00 ms`. In 16-node set: all-reduce 1 MiB `40.01 ms`. |
| `auh7-1b-gpu-200` | `206`, `267` | Healthy after cross-check | Failed with `206`, but `206` later reproduced the failure with `268`. With known-good `267`: all-reduce 1 MiB `0.683 ms`, 64 MiB `25.41 ms`, ring p2p 64 MiB `32.66 ms`. |
| `auh7-1b-gpu-206` | `200`, `268` | Comm failed | ROCm health passed, then ranks on `206` failed in both jobs with `torch.AcceleratorError: HIP error: invalid argument`; peer ranks later saw TCPStore/NCCL setup shutdown. |
| `auh7-1b-gpu-210` | `224` | Healthy / usable | With `224`: all-reduce 1 MiB `0.62 ms`, 64 MiB `13.42 ms`, ring p2p 64 MiB `30.51 ms`. |
| `auh7-1b-gpu-224` | `210` | Healthy / usable | With `210`: all-reduce 1 MiB `0.62 ms`, 64 MiB `13.42 ms`, ring p2p 64 MiB `30.51 ms`. |
| `auh7-1b-gpu-225` | `226` | Too slow / pair not isolated | With `226`: all-reduce 1 MiB `3.44 ms`, 64 MiB `54.74 ms`, ring p2p 64 MiB `78.99 ms`. |
| `auh7-1b-gpu-226` | `225` | Too slow / pair not isolated | With `225`: all-reduce 1 MiB `3.44 ms`, 64 MiB `54.74 ms`, ring p2p 64 MiB `78.99 ms`. |
| `auh7-1b-gpu-227` | `297`; healthy 8-node set `76346`; degraded 16-node set `76597` | Healthy | With `297`: all-reduce 1 MiB `0.65 ms`, 64 MiB `23.65 ms`. Healthy 8-node set `76346`: all-reduce 1 MiB `1.05 ms`, 64 MiB `35.32 ms`. The 16-node set was degraded and does not clear this node as 16-node healthy. |
| `auh7-1b-gpu-228` | `273`; 16-node set `76597` | Too slow / pair not isolated | With `273`: all-reduce 1 MiB `24.82 ms`, 64 MiB `92.93 ms`, same-local-rank 1 MiB about `19.75-19.81 ms`. In 16-node set: all-reduce 1 MiB `40.01 ms`. |
| `auh7-1b-gpu-240` | `252` | Healthy / usable | With `252`: all-reduce 1 MiB `0.61 ms`, 64 MiB `13.55 ms`, ring p2p 64 MiB `31.99 ms`. |
| `auh7-1b-gpu-252` | `240` | Healthy / usable | With `240`: all-reduce 1 MiB `0.61 ms`, 64 MiB `13.55 ms`, ring p2p 64 MiB `31.99 ms`. |
| `auh7-1b-gpu-267` | `268`, `275`, `200`; healthy 4-node set `76344`; healthy 8-node set `76346`; degraded 16-node set `76597` | Healthy | With `268`: all-reduce 1 MiB `0.579 ms`, 64 MiB `13.27 ms`. With `200`: all-reduce 1 MiB `0.683 ms`. `275` failure was isolated to `275`. Healthy 4-node set `76344`: all-reduce 1 MiB `0.77 ms`. The 16-node set was degraded and does not clear this node as 16-node healthy. |
| `auh7-1b-gpu-268` | `267`, `276`, `206`; healthy 4-node set `76344`; healthy 8-node set `76346`; degraded 16-node set `76597` | Healthy | With `267`: all-reduce 1 MiB `0.579 ms`, 64 MiB `13.27 ms`. `276` failure was isolated to `276`; `206` failure was isolated to `206`. Healthy 4-node set `76344`: all-reduce 1 MiB `0.77 ms`. The 16-node set was degraded and does not clear this node as 16-node healthy. |
| `auh7-1b-gpu-269` | `270`, `282`, `319`; healthy 4-node set `76344`; healthy 8-node set `76346`; degraded 16-node set `76597` | Healthy | With `270`: all-reduce 1 MiB `0.58 ms`, 64 MiB `12.89 ms`, ring p2p 64 MiB `31.75 ms`. Failures with `282` and `319` were isolated to those peers. Healthy 4-node set `76344`: all-reduce 1 MiB `0.77 ms`. The 16-node set was degraded and does not clear this node as 16-node healthy. |
| `auh7-1b-gpu-270` | `269`, `287`, `320`; healthy 4-node set `76344`; healthy 8-node set `76346`; degraded 16-node set `76597` | Healthy | With `287`: all-reduce 1 MiB `0.580 ms`, 64 MiB `13.27 ms`. With `320`: all-reduce 1 MiB `0.672 ms`, 64 MiB `25.66 ms`. Healthy 4-node set `76344`: all-reduce 1 MiB `0.77 ms`. The 16-node set was degraded and does not clear this node as 16-node healthy. |
| `auh7-1b-gpu-271` | `272`; 4-node degraded group; 16-node set `76597` | Too slow / pair not isolated | With `272`: all-reduce 1 MiB `3.05 ms`, 64 MiB `54.81 ms`, ring p2p 64 MiB `78.90 ms`. In 4-node degraded group: all-reduce 1 MiB `29.03 ms`. |
| `auh7-1b-gpu-272` | `271`; 4-node degraded group; 16-node set `76597` | Too slow / pair not isolated | With `271`: all-reduce 1 MiB `3.05 ms`, 64 MiB `54.81 ms`, ring p2p 64 MiB `78.90 ms`. In 4-node degraded group: all-reduce 1 MiB `29.03 ms`. |
| `auh7-1b-gpu-273` | `228`; 16-node set `76597` | Too slow / pair not isolated | With `228`: all-reduce 1 MiB `24.82 ms`, 64 MiB `92.93 ms`, same-local-rank 1 MiB about `19.75-19.81 ms`. In 16-node set: all-reduce 1 MiB `40.01 ms`. |
| `auh7-1b-gpu-274` | `317`; 16-node set `76597` | Too slow / pair not isolated | With `317`: all-reduce 1 MiB `3.40 ms`, 64 MiB `58.89 ms`, ring p2p 64 MiB `78.73 ms`. In 16-node set: all-reduce 1 MiB `40.01 ms`. |
| `auh7-1b-gpu-275` | `276`, `267` | Comm failed | RCCL `NET/IB` fatal completion on `rocep97s0f0`, `status=12`, `vendor err 10`, `local work queue catastrophic error`; reproduced with known-good `267`. |
| `auh7-1b-gpu-276` | `275`, `268` | Comm failed | RCCL `NET/IB` fatal completion on `rocep97s0f0`, `status=12`, `vendor err 10`, `local work queue catastrophic error`; reproduced with known-good `268`. |
| `auh7-1b-gpu-282` | `287`, `269` | Comm failed | RCCL `NET/IB` `status=12` / `vendor err 10`; reproduced with known-good `269`. `287` later passed with `270`. |
| `auh7-1b-gpu-284` | `285`; 4-node degraded group | Too slow / pair not isolated | With `285`: all-reduce 1 MiB `19.96 ms`, 64 MiB `93.00 ms`, same-local-rank 1 MiB up to `24.11 ms`. In 4-node degraded group: all-reduce 1 MiB `29.03 ms`. |
| `auh7-1b-gpu-285` | `284`; 4-node degraded group | Too slow / pair not isolated | With `284`: all-reduce 1 MiB `19.96 ms`, 64 MiB `93.00 ms`, same-local-rank 1 MiB up to `24.11 ms`. In 4-node degraded group: all-reduce 1 MiB `29.03 ms`. |
| `auh7-1b-gpu-286` | `296`; healthy 8-node set `76346`; degraded 16-node set `76597` | Healthy | With `296`: all-reduce 1 MiB `0.637 ms`, 64 MiB `24.14 ms`. Healthy 8-node set `76346`: all-reduce 1 MiB `1.05 ms`, 64 MiB `35.32 ms`. The 16-node set was degraded and does not clear this node as 16-node healthy. |
| `auh7-1b-gpu-287` | `282`, `270` | Healthy communication; SSH/PAM separate | Failed only when paired with bad `282`. Passed with `270`: all-reduce 1 MiB `0.580 ms`, 64 MiB `13.27 ms`, ring p2p 64 MiB `31.81 ms`. |
| `auh7-1b-gpu-296` | `286`; healthy 8-node set `76346`; degraded 16-node set `76597` | Healthy | With `286`: all-reduce 1 MiB `0.637 ms`, 64 MiB `24.14 ms`. Healthy 8-node set `76346`: all-reduce 1 MiB `1.05 ms`, 64 MiB `35.32 ms`. The 16-node set was degraded and does not clear this node as 16-node healthy. |
| `auh7-1b-gpu-297` | `227`; healthy 8-node set `76346`; degraded 16-node set `76597` | Healthy | With `227`: all-reduce 1 MiB `0.653 ms`, 64 MiB `23.65 ms`. Healthy 8-node set `76346`: all-reduce 1 MiB `1.05 ms`, 64 MiB `35.32 ms`. The 16-node set was degraded and does not clear this node as 16-node healthy. |
| `auh7-1b-gpu-317` | `274`; 16-node set `76597` | Too slow / pair not isolated | With `274`: all-reduce 1 MiB `3.40 ms`, 64 MiB `58.89 ms`, ring p2p 64 MiB `78.73 ms`. In 16-node set: all-reduce 1 MiB `40.01 ms`. |
| `auh7-1b-gpu-319` | `320`, `269` | Comm failed | RCCL `NET/IB` fatal completion on `rocep97s0f0`, `status=12`, `vendor err 10`, `local work queue catastrophic error`; reproduced with known-good `269`. |
| `auh7-1b-gpu-320` | `319`, `270` | Healthy after cross-check | Failed only when paired with bad `319`. Passed with `270`: all-reduce 1 MiB `0.672 ms`, 64 MiB `25.66 ms`, ring p2p 64 MiB `30.48 ms`. |

## Current Communication Guidance

Exclude for communication correctness:

- `auh7-1b-gpu-206`
- `auh7-1b-gpu-275`
- `auh7-1b-gpu-276`
- `auh7-1b-gpu-282`
- `auh7-1b-gpu-319`

Treat as degraded communication paths unless additional cross-checks clear them:

- `auh7-1b-gpu-[196-197]`
- `auh7-1b-gpu-[225-226]`
- `auh7-1b-gpu-228` with `auh7-1b-gpu-273`
- `auh7-1b-gpu-[271-272]`
- `auh7-1b-gpu-274` with `auh7-1b-gpu-317`
- `auh7-1b-gpu-[284-285]`

Current healthier nodes from completed checks:

- `auh7-1b-gpu-200`
- `auh7-1b-gpu-210`
- `auh7-1b-gpu-224`
- `auh7-1b-gpu-227`
- `auh7-1b-gpu-240`
- `auh7-1b-gpu-252`
- `auh7-1b-gpu-[267-270]`
- `auh7-1b-gpu-[286-287]`
- `auh7-1b-gpu-[296-297]`
- `auh7-1b-gpu-320`

No clean 16-node communication-healthy set has been validated in these artifacts.
The completed 16-node job `76597` avoided known hard-failing nodes but included
known degraded paths, so it should be used only as evidence of scale-dependent
degradation.
