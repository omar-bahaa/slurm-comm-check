#!/bin/bash
#SBATCH --job-name=comm-check
#SBATCH --partition=faculty
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:mi210:8
#SBATCH --mem=2048G
#SBATCH --exclusive
#SBATCH --output=logs/%x.%j.out
#SBATCH --error=logs/%x.%j.err

set -euo pipefail

EXPECTED_NUM_NODES="${EXPECTED_NUM_NODES:-${SLURM_NNODES:-2}}"
GPUS_PER_NODE="${GPUS_PER_NODE:-8}"
MASTER_PORT="${MASTER_PORT:-$((6400 + SLURM_JOB_ID % 1000))}"
RUN_LABEL="${RUN_LABEL:-nodes${EXPECTED_NUM_NODES}}"
COMM_TIMEOUT_SECONDS="${COMM_TIMEOUT_SECONDS:-1800}"
COMM_WARMUP_ITERS="${COMM_WARMUP_ITERS:-2}"
COMM_MEASURE_ITERS="${COMM_MEASURE_ITERS:-5}"
COMM_TIMEOUT_MINUTES="${COMM_TIMEOUT_MINUTES:-20}"
COMM_SIZES_BYTES="${COMM_SIZES_BYTES:-4,4096,1048576,16777216,67108864}"
COMM_GATHER_SIZES_BYTES="${COMM_GATHER_SIZES_BYTES:-4,4096,1048576}"
COMM_SUBGROUP_SIZES_BYTES="${COMM_SUBGROUP_SIZES_BYTES:-4,1048576,16777216}"

REPO_DIR="${REPO_DIR:-${SLURM_SUBMIT_DIR:-$(pwd)}}"
SCRIPT_DIR="${SCRIPT_DIR:-${REPO_DIR}}"
RUN_ROOT="${RUN_ROOT:-${SCRIPT_DIR}/runs}"
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
RUN_DIR="${RUN_ROOT}/${SLURM_JOB_ID}_${RUN_LABEL}"
NODES_FILE="${RUN_DIR}/allocated_nodes.txt"
STEP_SCRIPT="${RUN_DIR}/comm_check_step.sh"

VENV_PATH="${VENV_PATH:-${SCRIPT_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-${VENV_PATH}/bin/python}"
TORCHRUN_BIN="${TORCHRUN_BIN:-${VENV_PATH}/bin/torchrun}"
ROCM_PATH="${ROCM_PATH:-/opt/rocm-7.0.0}"

NCCL_P2P_DISABLE="${NCCL_P2P_DISABLE:-0}"
NCCL_IB_HCA="${NCCL_IB_HCA:-rocep97s0f0}"
NCCL_SOCKET_IFNAME="${NCCL_SOCKET_IFNAME:-bond0}"
NCCL_CROSS_NIC="${NCCL_CROSS_NIC:-0}"
NCCL_DEBUG="${NCCL_DEBUG:-WARN}"
TORCH_NCCL_ASYNC_ERROR_HANDLING="${TORCH_NCCL_ASYNC_ERROR_HANDLING:-1}"

mkdir -p "${RUN_DIR}" "${LOG_DIR}"

validate_python_env() {
  if [[ ! -x "${PYTHON_BIN}" ]]; then
    echo "ERROR: Python executable not found: ${PYTHON_BIN}" >&2
    echo "Create the default environment with: scripts/setup_rocm_venv.sh" >&2
    echo "Or pass VENV_PATH, PYTHON_BIN, and TORCHRUN_BIN explicitly." >&2
    exit 1
  fi
  if [[ ! -x "${TORCHRUN_BIN}" ]]; then
    echo "ERROR: torchrun executable not found: ${TORCHRUN_BIN}" >&2
    echo "Create the default environment with: scripts/setup_rocm_venv.sh" >&2
    echo "Or pass VENV_PATH, PYTHON_BIN, and TORCHRUN_BIN explicitly." >&2
    exit 1
  fi
}

validate_python_env
cd "${REPO_DIR}"

echo "Job ID: ${SLURM_JOB_ID}"
echo "Repo: ${REPO_DIR}"
echo "Script dir: ${SCRIPT_DIR}"
echo "Run label: ${RUN_LABEL}"
echo "Run dir: ${RUN_DIR}"
echo "Expected nodes: ${EXPECTED_NUM_NODES}"
echo "Slurm nodelist: ${SLURM_JOB_NODELIST}"
echo "GPUs per node: ${GPUS_PER_NODE}"
echo "Master port: ${MASTER_PORT}"
echo "Venv path: ${VENV_PATH}"
echo "Python: $(${PYTHON_BIN} --version 2>&1)"
echo "Torchrun: ${TORCHRUN_BIN}"

scontrol show hostnames "${SLURM_JOB_NODELIST}" > "${NODES_FILE}"
mapfile -t ALLOCATED_NODES < "${NODES_FILE}"

if [[ "${#ALLOCATED_NODES[@]}" -ne "${EXPECTED_NUM_NODES}" ]]; then
  echo "ERROR: expected ${EXPECTED_NUM_NODES} allocated nodes but Slurm returned ${#ALLOCATED_NODES[@]}" >&2
  cat "${NODES_FILE}" >&2
  exit 1
fi

MASTER_ADDR="${MASTER_ADDR:-${ALLOCATED_NODES[0]}}"

echo "Allocated nodes:"
cat "${NODES_FILE}"
echo "Master node: ${MASTER_ADDR}:${MASTER_PORT}"

export REPO_DIR
export SCRIPT_DIR
export RUN_DIR
export VENV_PATH
export PYTHON_BIN
export TORCHRUN_BIN
export ROCM_PATH
export EXPECTED_NUM_NODES
export GPUS_PER_NODE
export MASTER_ADDR
export MASTER_PORT
export COMM_TIMEOUT_SECONDS
export COMM_WARMUP_ITERS
export COMM_MEASURE_ITERS
export COMM_TIMEOUT_MINUTES
export COMM_SIZES_BYTES
export COMM_GATHER_SIZES_BYTES
export COMM_SUBGROUP_SIZES_BYTES
export NCCL_P2P_DISABLE
export NCCL_IB_HCA
export NCCL_SOCKET_IFNAME
export NCCL_CROSS_NIC
export NCCL_DEBUG
export TORCH_NCCL_ASYNC_ERROR_HANDLING

cat > "${STEP_SCRIPT}" <<'EOF'
#!/bin/bash
set -euo pipefail

cd "${REPO_DIR}"

if [[ -d "${ROCM_PATH}/bin" ]]; then
  export PATH="${ROCM_PATH}/bin:${PATH}"
fi

current_host="$(hostname -s 2>/dev/null || hostname)"
node_rank="${SLURM_NODEID}"
node_log_prefix="${RUN_DIR}/node${node_rank}_${current_host}"
visible_devices="$(seq -s, 0 "$((GPUS_PER_NODE - 1))")"

{
  echo "host=${current_host}"
  echo "node_rank=${node_rank}"
  echo "date=$(date -Is)"
  echo "PATH=${PATH}"
  echo "ROCM_PATH=${ROCM_PATH}"
  echo "which rocm-smi=$(command -v rocm-smi || true)"
  echo "rocm_path_exists=$([[ -d "${ROCM_PATH}" ]] && echo yes || echo no)"
  rocm-smi
} > "${node_log_prefix}_health.log" 2>&1

export GPUS_PER_NODE
export MASTER_ADDR
export MASTER_PORT
export ROCR_VISIBLE_DEVICES="${ROCR_VISIBLE_DEVICES:-${visible_devices}}"
export COMM_WARMUP_ITERS
export COMM_MEASURE_ITERS
export COMM_TIMEOUT_MINUTES
export COMM_SIZES_BYTES
export COMM_GATHER_SIZES_BYTES
export COMM_SUBGROUP_SIZES_BYTES
export COMM_OUTPUT_JSON="${RUN_DIR}/comm_metrics.json"

{
  echo "host=${current_host}"
  echo "node_rank=${node_rank}"
  echo "master=${MASTER_ADDR}:${MASTER_PORT}"
  echo "ROCR_VISIBLE_DEVICES=${ROCR_VISIBLE_DEVICES}"
  echo "NCCL_P2P_DISABLE=${NCCL_P2P_DISABLE}"
  echo "NCCL_IB_HCA=${NCCL_IB_HCA}"
  echo "NCCL_SOCKET_IFNAME=${NCCL_SOCKET_IFNAME}"
  echo "NCCL_CROSS_NIC=${NCCL_CROSS_NIC}"
  echo "NCCL_DEBUG=${NCCL_DEBUG}"
  echo "TORCH_NCCL_ASYNC_ERROR_HANDLING=${TORCH_NCCL_ASYNC_ERROR_HANDLING}"
  echo "COMM_WARMUP_ITERS=${COMM_WARMUP_ITERS}"
  echo "COMM_MEASURE_ITERS=${COMM_MEASURE_ITERS}"
  echo "COMM_TIMEOUT_MINUTES=${COMM_TIMEOUT_MINUTES}"
  echo "COMM_SIZES_BYTES=${COMM_SIZES_BYTES}"
  echo "COMM_GATHER_SIZES_BYTES=${COMM_GATHER_SIZES_BYTES}"
  echo "COMM_SUBGROUP_SIZES_BYTES=${COMM_SUBGROUP_SIZES_BYTES}"
  echo "date=$(date -Is)"
  timeout "${COMM_TIMEOUT_SECONDS}s" "${TORCHRUN_BIN}" \
    --nproc_per_node "${GPUS_PER_NODE}" \
    --nnodes "${EXPECTED_NUM_NODES}" \
    --node_rank "${node_rank}" \
    --master_addr "${MASTER_ADDR}" \
    --master_port "${MASTER_PORT}" \
    "${SCRIPT_DIR}/comm_benchmark.py"
} > "${node_log_prefix}_torchrun.log" 2>&1
EOF
chmod +x "${STEP_SCRIPT}"

echo "Starting communication benchmark through Slurm tasks"
srun \
  --nodes="${EXPECTED_NUM_NODES}" \
  --ntasks="${EXPECTED_NUM_NODES}" \
  --ntasks-per-node=1 \
  --kill-on-bad-exit=1 \
  --export=ALL \
  "${STEP_SCRIPT}"

"${PYTHON_BIN}" "${SCRIPT_DIR}/summarize_comm_results.py" \
  --run-dir "${RUN_DIR}" \
  | tee "${RUN_DIR}/summary.txt"

echo "Communication benchmark finished for job ${SLURM_JOB_ID}"
