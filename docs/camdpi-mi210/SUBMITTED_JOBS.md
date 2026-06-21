# Submitted Communication Jobs

| Job ID | Nodes | Node List | Label | State | Result |
|---|---:|---|---|---|---|
| 76325 | 2 | auh7-1b-gpu-[275-276] | validation_2node | CANCELLED | ROCm health passed; RCCL failed with `NET/IB` status=12/vendor err 10 on `rocep97s0f0` before metrics completed. Also exposed an sbatch export bug for comma-separated size lists, now fixed. |
| 76326 | 2 | auh7-1b-gpu-[257-258] | validation_257_258 | CANCELLED | Pending on resources because `257` was allocated and `258` was mixed; no benchmark ran. |
| 76327 | 2 | auh7-1b-gpu-[267-268] | validation_267_268 | COMPLETED | Healthy baseline. Metrics and summary written in `runs/76327_validation_267_268`; no suspicious thresholds crossed. |
| 76329 | 2 | auh7-1b-gpu-[224-225] | pair_224_225 | CANCELLED | Pending on resources after both nodes became allocated by other work; no benchmark ran. |
| 76330 | 2 | auh7-1b-gpu-226, auh7-1b-gpu-287 | pair_226_287 | CANCELLED | Pending on resources after `226` became allocated by other work; no benchmark ran. |
| 76331 | 2 | auh7-1b-gpu-267, auh7-1b-gpu-275 | cross_267_275 | CANCELLED | `275` failed against healthy `267` with RCCL `NET/IB` status=12/vendor err 10 on `rocep97s0f0`; canceled after evidence was captured. |
| 76332 | 2 | auh7-1b-gpu-268, auh7-1b-gpu-276 | cross_268_276 | CANCELLED | `276` failed against healthy `268` with RCCL `NET/IB` status=12/vendor err 10 on `rocep97s0f0`; canceled after evidence was captured. |
| 76333 | 2 | auh7-1b-gpu-[269-270] | pair_269_270 | COMPLETED | Healthy. World all-reduce 1 MiB p95 0.58 ms, 64 MiB p95 12.89 ms, ring p2p 64 MiB p95 31.75 ms. |
| 76334 | 2 | auh7-1b-gpu-[271-272] | pair_271_272 | COMPLETED | Degraded but completed. World all-reduce 1 MiB p95 3.05 ms and 64 MiB p95 54.81 ms; ring p2p 64 MiB p95 78.90 ms. |
| 76335 | 2 | auh7-1b-gpu-282, auh7-1b-gpu-287 | pair_282_287 | CANCELLED | Failed with RCCL `NET/IB` status=12/vendor err 10; later cross-check isolated `282` as the communication-bad node while `287` passed with `270`. |
| 76336 | 2 | auh7-1b-gpu-[284-285] | pair_284_285 | COMPLETED | Severely degraded but completed. World all-reduce 1 MiB p95 19.96 ms and 64 MiB p95 93.00 ms; same-local-rank 1 MiB all-reduce as slow as 24.11 ms. |
| 76337 | 2 | auh7-1b-gpu-286, auh7-1b-gpu-296 | pair_286_296 | COMPLETED | Mostly healthy. World all-reduce 1 MiB p95 0.64 ms; 64 MiB p95 24.14 ms. |
| 76338 | 2 | auh7-1b-gpu-297, auh7-1b-gpu-227 | pair_297_227 | COMPLETED | Mostly healthy. World all-reduce 1 MiB p95 0.65 ms; 64 MiB p95 23.65 ms. |
| 76340 | 2 | auh7-1b-gpu-269, auh7-1b-gpu-282 | cross_269_282 | CANCELLED | `282` failed against healthy `269` with RCCL `NET/IB` status=12/vendor err 10; canceled after evidence was captured. |
| 76341 | 2 | auh7-1b-gpu-270, auh7-1b-gpu-287 | cross_270_287 | COMPLETED | `287` passed NCCL/RCCL communication with healthy `270`; its earlier issue is likely SSH/PAM orchestration-specific, not communication-specific. |
| 76344 | 4 | auh7-1b-gpu-[267-270] | 4node_267_270 | COMPLETED | Healthy 4-node baseline. World all-reduce 1 MiB p95 0.77 ms, 64 MiB p95 23.90 ms; ring p2p 64 MiB p95 32.20 ms. |
| 76345 | 4 | auh7-1b-gpu-[271-272,284-285] | 4node_degraded_271_272_284_285 | COMPLETED | Degraded 4-node group. World all-reduce 1 MiB p95 29.03 ms; same-local-rank 1 MiB all-reduce p95 about 31.3 ms; 16 MiB same-local-rank p95 about 74.7 ms. |
| 76346 | 8 | auh7-1b-gpu-227, auh7-1b-gpu-[267-270], auh7-1b-gpu-286, auh7-1b-gpu-[296-297] | 8node_best_current | COMPLETED | Healthy 8-node run. World all-reduce 1 MiB p95 1.05 ms, 64 MiB p95 35.32 ms; ring p2p 64 MiB p95 35.26 ms. |
| 76349 | 2 | auh7-1b-gpu-210, auh7-1b-gpu-224 | pair_210_224 | COMPLETED | Usable. World all-reduce 1 MiB p95 0.62 ms, 64 MiB p95 13.42 ms; ring p2p 64 MiB p95 30.51 ms. |
| 76350 | 2 | auh7-1b-gpu-[225-226] | pair_225_226 | COMPLETED | Degraded. World all-reduce 1 MiB p95 3.44 ms, 64 MiB p95 54.74 ms; ring p2p 64 MiB p95 78.99 ms. |
| 76351 | 2 | auh7-1b-gpu-240, auh7-1b-gpu-252 | pair_240_252 | COMPLETED | Usable. World all-reduce 1 MiB p95 0.61 ms, 64 MiB p95 13.55 ms; ring p2p 64 MiB p95 31.99 ms. |
| 76354 | 16 | auh7-1b-gpu-210, auh7-1b-gpu-[224-227], auh7-1b-gpu-240, auh7-1b-gpu-252, auh7-1b-gpu-[267-271], auh7-1b-gpu-[286-287], auh7-1b-gpu-[296-297] | 16node_best_available | CANCELLED | Pending on resources after `224-226` were allocated by other work; no benchmark ran. |
| 76361 | 16 | auh7-1b-gpu-227, auh7-1b-gpu-240, auh7-1b-gpu-252, auh7-1b-gpu-[267-272], auh7-1b-gpu-282, auh7-1b-gpu-[284-287], auh7-1b-gpu-[296-297] | 16node_available_with_bad_282 | CANCELLED | Pending on resources because required nodes became `mixed-`; no benchmark ran. This was not a clean candidate anyway because it included known-bad `282`. |
| 76592 | 2 | auh7-1b-gpu-[196-197] | pair_196_197 | COMPLETED | Degraded. World all-reduce 1 MiB p95 3.37 ms, 64 MiB p95 54.78 ms; ring p2p 64 MiB p95 79.00 ms. |
| 76593 | 2 | auh7-1b-gpu-200, auh7-1b-gpu-206 | pair_200_206 | FAILED | No metrics. ROCm health passed, then `206` ranks failed during distributed setup/object gather with `torch.AcceleratorError: HIP error: invalid argument`; later cross-checks isolated `206` as bad while `200` passed. |
| 76594 | 2 | auh7-1b-gpu-228, auh7-1b-gpu-273 | pair_228_273 | COMPLETED | Severely degraded. World all-reduce 1 MiB p95 24.82 ms, 64 MiB p95 92.93 ms; same-local-rank 1 MiB all-reduce about 19.75-19.81 ms. |
| 76595 | 2 | auh7-1b-gpu-274, auh7-1b-gpu-317 | pair_274_317 | COMPLETED | Degraded. World all-reduce 1 MiB p95 3.40 ms, 64 MiB p95 58.89 ms; ring p2p 64 MiB p95 78.73 ms. |
| 76596 | 2 | auh7-1b-gpu-[319-320] | pair_319_320 | CANCELLED | Failed/hung with RCCL `NET/IB` status=12/vendor err 10. Later cross-check isolated `319` as bad while `320` passed with `270`. |
| 76597 | 16 | auh7-1b-gpu-[196-197], auh7-1b-gpu-227, auh7-1b-gpu-228, auh7-1b-gpu-[267-274], auh7-1b-gpu-286, auh7-1b-gpu-[296-297], auh7-1b-gpu-317 | 16node_degraded_no_fatal_known | COMPLETED | Completed without hard RCCL fatal, but very slow. World all-reduce 1 MiB p95 40.01 ms, 64 MiB p95 56.91 ms; same-local-rank 1 MiB p95 about 40.8 ms. |
| 76599 | 2 | auh7-1b-gpu-200, auh7-1b-gpu-267 | cross_200_267 | COMPLETED | `200` passed with known-good `267`. World all-reduce 1 MiB p95 0.683 ms, 64 MiB p95 25.41 ms; ring p2p 64 MiB p95 32.66 ms. |
| 76600 | 2 | auh7-1b-gpu-206, auh7-1b-gpu-268 | cross_206_268 | FAILED | `206` failed again with known-good `268`; `206` ranks hit `torch.AcceleratorError: HIP error: invalid argument`, and `268` ranks later reported TCPStore peer shutdown. |
| 76601 | 2 | auh7-1b-gpu-319, auh7-1b-gpu-269 | cross_319_269 | CANCELLED | `319` failed with known-good `269` using RCCL `NET/IB` status=12/vendor err 10 on `rocep97s0f0`; canceled after evidence was captured. |
| 76602 | 2 | auh7-1b-gpu-320, auh7-1b-gpu-270 | cross_320_270 | COMPLETED | `320` passed with known-good `270`. World all-reduce 1 MiB p95 0.672 ms, 64 MiB p95 25.66 ms; ring p2p 64 MiB p95 30.48 ms. |
