# Slurm GPU Communication Check

`slurm-comm-check` is a small Slurm-friendly benchmark for checking multinode GPU
communication health before running distributed training or other collective-heavy
workloads.

The benchmark launches one `torchrun` worker per GPU on each allocated Slurm node
and measures the communication patterns that commonly expose cluster issues:

- process-group initialization and the first distributed barrier
- global `all_reduce`, `broadcast`, `all_gather`, and `reduce_scatter`
- ring and pair point-to-point transfers
- node-local all-reduce groups
- same-local-rank cross-node all-reduce groups
- per-node ROCm, `rocm-smi`, PyTorch, HIP, and visible-device health

It has no Python package dependency beyond the PyTorch environment you already use
for distributed training.

## Reproducible Setup Branch

The `main` branch is kept as the default branch and currently preserves the
original CAMDPI/user-specific Slurm and Python setup used during the investigation.

For a reproducible setup that creates a repo-local Python virtual environment and
installs PyTorch for ROCm 7.0 with:

```bash
pip install --index-url https://download.pytorch.org/whl/rocm7.0 torch torchvision torchaudio
```

use the `venv-rocm7-setup` branch:

```bash
git clone --branch venv-rocm7-setup https://github.com/omar-bahaa/slurm-comm-check.git
cd slurm-comm-check
scripts/setup_rocm_venv.sh
```

If you already cloned this repository:

```bash
git fetch origin
git switch venv-rocm7-setup
scripts/setup_rocm_venv.sh
```

## Requirements

- Slurm
- GPU nodes allocated exclusively or otherwise free enough for full-node testing
- Python with PyTorch installed
- `torchrun` on `PATH`
- ROCm clusters: `rocm-smi` on `PATH`

The default `run_comm_check.sbatch` settings match the CAMDPI MI210 Slurm setup:

- partition: `faculty`
- QoS: `qirong_qos`
- GPUs: `gpu:mi210:8`
- memory: `2048G`
- node mode: `--exclusive`
- ROCm path: `/opt/rocm-7.0.0`
- NCCL/RCCL network defaults: `NCCL_SOCKET_IFNAME=bond0`,
  `NCCL_IB_HCA=rocep97s0f0`

Edit the `#SBATCH` lines or pass environment overrides if your cluster differs.

## Quick Start

Clone the repository and submit a two-node smoke check:

```bash
git clone https://github.com/omar-bahaa/slurm-comm-check.git
cd slurm-comm-check
mkdir -p logs runs

sbatch --nodes=2 \
  --export=ALL,EXPECTED_NUM_NODES=2,CONDA_ENV=omar_mg7,CONDA_INIT_SCRIPT=/vast/users/qirong.ho/miniforge3/etc/profile.d/conda.sh,RUN_LABEL=pair_smoke \
  run_comm_check.sbatch
```

For a fixed pair of nodes:

```bash
sbatch --nodes=2 \
  --nodelist=auh7-1b-gpu-[267-268] \
  --export=ALL,EXPECTED_NUM_NODES=2,CONDA_ENV=omar_mg7,CONDA_INIT_SCRIPT=/vast/users/qirong.ho/miniforge3/etc/profile.d/conda.sh,RUN_LABEL=pair_267_268 \
  run_comm_check.sbatch
```

For larger checks:

```bash
sbatch --nodes=4 \
  --export=ALL,EXPECTED_NUM_NODES=4,CONDA_ENV=omar_mg7,CONDA_INIT_SCRIPT=/vast/users/qirong.ho/miniforge3/etc/profile.d/conda.sh,RUN_LABEL=4node_check \
  run_comm_check.sbatch

sbatch --nodes=8 \
  --export=ALL,EXPECTED_NUM_NODES=8,CONDA_ENV=omar_mg7,CONDA_INIT_SCRIPT=/vast/users/qirong.ho/miniforge3/etc/profile.d/conda.sh,RUN_LABEL=8node_check \
  run_comm_check.sbatch

sbatch --nodes=16 \
  --export=ALL,EXPECTED_NUM_NODES=16,CONDA_ENV=omar_mg7,CONDA_INIT_SCRIPT=/vast/users/qirong.ho/miniforge3/etc/profile.d/conda.sh,RUN_LABEL=16node_check \
  run_comm_check.sbatch
```

If you do not use conda, leave `CONDA_ENV` unset and make sure `python` and
`torchrun` are available in the job environment. You can also set `PYTHON_BIN`
and `TORCHRUN_BIN`.

## Outputs

Each job writes a self-contained run directory:

```text
runs/<slurm_job_id>_<run_label>/
  allocated_nodes.txt
  comm_check_step.sh
  comm_metrics.json
  summary.txt
  node<N>_<hostname>_health.log
  node<N>_<hostname>_torchrun.log
```

Slurm stdout/stderr goes to:

```text
logs/comm-check.<job_id>.out
logs/comm-check.<job_id>.err
```

The most useful files are:

- `summary.txt`: human-readable health and latency summary.
- `comm_metrics.json`: structured metrics for comparison or downstream analysis.
- `node*_torchrun.log`: NCCL/RCCL, torch distributed, timeout, and transport
  errors.
- `node*_health.log`: `rocm-smi`, environment, and device visibility checks.

## Configuration

The sbatch script exposes the main knobs through environment variables:

| Variable | Default | Meaning |
|---|---:|---|
| `EXPECTED_NUM_NODES` | `SLURM_NNODES` | Fails fast if Slurm allocated a different number of nodes. |
| `GPUS_PER_NODE` | `8` | Number of ranks launched per node. |
| `RUN_LABEL` | `nodes<N>` | Suffix for the run directory. |
| `CONDA_ENV` | empty | Optional conda environment to activate. |
| `CONDA_INIT_SCRIPT` | empty | Optional conda initialization script. |
| `PYTHON_BIN` | `python` | Python executable used for summarization. |
| `TORCHRUN_BIN` | `torchrun` | Torch distributed launcher. |
| `ROCM_PATH` | `/opt/rocm-7.0.0` | ROCm installation path to prepend to `PATH` and record in health checks. |
| `MASTER_PORT` | job-derived | Torch distributed rendezvous port. |
| `COMM_TIMEOUT_SECONDS` | `1800` | Outer per-node `torchrun` timeout. |
| `COMM_TIMEOUT_MINUTES` | `20` | PyTorch process-group timeout. |
| `COMM_WARMUP_ITERS` | `2` | Warmup iterations per measured operation. |
| `COMM_MEASURE_ITERS` | `5` | Timed iterations per measured operation. |
| `COMM_SIZES_BYTES` | `4,4096,1048576,16777216,67108864` | Message sizes for global collectives and p2p. |
| `COMM_GATHER_SIZES_BYTES` | `4,4096,1048576` | Message sizes for all-gather and reduce-scatter. |
| `COMM_SUBGROUP_SIZES_BYTES` | `4,1048576,16777216` | Message sizes for node-local and same-local-rank subgroup all-reduce. |
| `NCCL_P2P_DISABLE` | `0` | Passed through to NCCL/RCCL. |
| `NCCL_IB_HCA` | `rocep97s0f0` | NIC/HCA selector for the default MI210 cluster. |
| `NCCL_SOCKET_IFNAME` | `bond0` | Socket interface selector for the default MI210 cluster. |
| `NCCL_CROSS_NIC` | `0` | Passed through to NCCL/RCCL. |
| `NCCL_DEBUG` | `WARN` | NCCL/RCCL logging level. |

## Interpreting Results

A healthy two-node run should complete cleanly, produce `comm_metrics.json`, and
show no suspicious metrics in `summary.txt`.

Common failure signals:

- `rocm-smi` fails or PyTorch sees fewer GPUs than expected: node software or
  visibility problem.
- `init_process_group` or first barrier is slow or times out: distributed
  rendezvous, network, firewall, Slurm launch, or bad-node issue.
- RCCL/NCCL `NET/IB` fatal completions: likely fabric, NIC, HCA, or node-level
  communication failure.
- A node passes with one partner but fails or slows with another: test against a
  known-good partner before blaming either endpoint.
- Two-node pairs pass but larger groups degrade: scale-dependent fabric or route
  issue; repeat 4-node, 8-node, and 16-node checks with overlapping node sets.

The benchmark is a health check, not an application throughput model. Use it to
find nodes, node pairs, or scale points that break basic GPU communication.

## Historical CAMDPI MI210 Notes

The `docs/camdpi-mi210/` directory contains the node-classification notes from
the investigation that motivated this tool. Those files are examples of how to
record pairwise and scale-dependent findings; they are not required to run the
benchmark.
