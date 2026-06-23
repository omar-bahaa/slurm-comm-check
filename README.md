# Slurm GPU Communication Check

`slurm-comm-check` is a small Slurm-friendly benchmark for checking multinode GPU
communication health before running distributed training or other collective-heavy
workloads.

The benchmark launches one `torchrun` worker per GPU on each allocated Slurm node
and measures communication patterns that commonly expose cluster issues:

- process-group initialization and the first distributed barrier
- global `all_reduce`, `broadcast`, `all_gather`, and `reduce_scatter`
- ring and pair point-to-point transfers
- node-local all-reduce groups
- same-local-rank cross-node all-reduce groups
- per-node ROCm, `rocm-smi`, PyTorch, HIP, and visible-device health

The repository is designed to run from a repo-local Python virtual environment.
It does not require conda and does not assume any user-specific Python path.

## Requirements

- Slurm
- Linux GPU nodes with ROCm installed
- Python 3 with `venv`
- `rocm-smi` available through the ROCm installation
- GPU nodes allocated exclusively or otherwise free enough for full-node testing

The checked-in `run_comm_check.sbatch` has practical CAMD MI210-style defaults:

- partition: `faculty`
- GPUs per node: `gpu:mi210:8`
- memory: `2048G`
- node mode: `--exclusive`
- ROCm path: `/opt/rocm-7.0.0`
- RCCL/NCCL network defaults: `NCCL_SOCKET_IFNAME=bond0`,
  `NCCL_IB_HCA=rocep97s0f0`

Edit the `#SBATCH` lines or pass Slurm options at submit time if your cluster
uses different partition, GPU, memory, QoS, or node-selection settings.

## Set Up the Python Environment

Clone the repository:

```bash
git clone --branch venv-rocm7-setup https://github.com/omar-bahaa/slurm-comm-check.git
cd slurm-comm-check
```

Until this setup flow is merged to `main`, use the `venv-rocm7-setup` branch as
shown above. If you already cloned the repository, run:

```bash
git fetch origin
git switch venv-rocm7-setup
```

Create the default repo-local virtual environment:

```bash
scripts/setup_rocm_venv.sh
```

By default, the setup script creates `.venv` and installs ROCm-enabled PyTorch
from:

```text
https://download.pytorch.org/whl/rocm7.0
```

This follows the PyTorch/pip installation model for ROCm wheels. If your site
uses a different ROCm wheel source or mirror, override the index URL:

```bash
PYTORCH_INDEX_URL=https://download.pytorch.org/whl/rocm7.0 \
  scripts/setup_rocm_venv.sh
```

If ROCm is installed somewhere other than `/opt/rocm-7.0.0`, pass `ROCM_PATH`:

```bash
ROCM_PATH=/path/to/rocm-7.0.0 scripts/setup_rocm_venv.sh
```

If you want the virtual environment somewhere else, pass `VENV_PATH`:

```bash
VENV_PATH=/path/to/slurm-comm-check-venv scripts/setup_rocm_venv.sh
```

The setup script verifies that the installed `torch` is a ROCm/HIP build and
that PyTorch can see a ROCm GPU. Run setup on a GPU node, or in an interactive
GPU allocation, so the verification step can see hardware.

Manual setup is equivalent to:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install --index-url https://download.pytorch.org/whl/rocm7.0 torch torchvision torchaudio
python - <<'PY'
import torch
print(torch.__version__)
print(getattr(torch.version, "hip", None))
print(torch.cuda.is_available())
print(torch.cuda.device_count())
PY
```

For current PyTorch ROCm wheel availability, check the official PyTorch selector
and AMD ROCm PyTorch installation documentation.

## Quick Start

Submit a two-node smoke check using the default `.venv`:

```bash
mkdir -p logs runs

sbatch --nodes=2 \
  --export=ALL,EXPECTED_NUM_NODES=2,RUN_LABEL=pair_smoke \
  run_comm_check.sbatch
```

For a fixed pair of nodes:

```bash
sbatch --nodes=2 \
  --nodelist=auh7-1b-gpu-[267-268] \
  --export=ALL,EXPECTED_NUM_NODES=2,RUN_LABEL=pair_267_268 \
  run_comm_check.sbatch
```

For larger checks:

```bash
sbatch --nodes=4 \
  --export=ALL,EXPECTED_NUM_NODES=4,RUN_LABEL=4node_check \
  run_comm_check.sbatch

sbatch --nodes=8 \
  --export=ALL,EXPECTED_NUM_NODES=8,RUN_LABEL=8node_check \
  run_comm_check.sbatch

sbatch --nodes=16 \
  --export=ALL,EXPECTED_NUM_NODES=16,RUN_LABEL=16node_check \
  run_comm_check.sbatch
```

If you created the venv outside the repository, pass `VENV_PATH`:

```bash
sbatch --nodes=2 \
  --export=ALL,EXPECTED_NUM_NODES=2,VENV_PATH=/path/to/slurm-comm-check-venv,RUN_LABEL=pair_smoke \
  run_comm_check.sbatch
```

If you need site-specific Slurm options, pass them to `sbatch`:

```bash
sbatch --partition=<partition> --qos=<qos> --nodes=2 \
  --export=ALL,EXPECTED_NUM_NODES=2,RUN_LABEL=pair_smoke \
  run_comm_check.sbatch
```

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
| `VENV_PATH` | `<repo>/.venv` | Python virtual environment used by the benchmark. |
| `PYTHON_BIN` | `$VENV_PATH/bin/python` | Python executable used for summarization. |
| `TORCHRUN_BIN` | `$VENV_PATH/bin/torchrun` | Torch distributed launcher. |
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
| `NCCL_IB_HCA` | `rocep97s0f0` | NIC/HCA selector for the default MI210 cluster. Override for other clusters. |
| `NCCL_SOCKET_IFNAME` | `bond0` | Socket interface selector for the default MI210 cluster. Override for other clusters. |
| `NCCL_CROSS_NIC` | `0` | Passed through to NCCL/RCCL. |
| `NCCL_DEBUG` | `WARN` | NCCL/RCCL logging level. |

The venv setup script also accepts:

| Variable | Default | Meaning |
|---|---:|---|
| `VENV_PATH` | `<repo>/.venv` | Where to create or reuse the virtual environment. |
| `PYTHON_BIN` | `python3` | Python executable used to create the venv. |
| `PYTORCH_INDEX_URL` | `https://download.pytorch.org/whl/rocm7.0` | PyTorch wheel index. |
| `ROCM_PATH` | `/opt/rocm-7.0.0` | ROCm path used for verification. |

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

## Historical CAMD MI210 Notes

The `docs/camd-mi210/` directory contains the node-classification notes from
the investigation that motivated this tool. Those files are examples of how to
record pairwise and scale-dependent findings; they are not required to run the
benchmark.
