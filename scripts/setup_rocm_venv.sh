#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

VENV_PATH="${VENV_PATH:-${SCRIPT_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTORCH_INDEX_URL="${PYTORCH_INDEX_URL:-https://download.pytorch.org/whl/rocm7.0}"
ROCM_PATH="${ROCM_PATH:-/opt/rocm-7.0.0}"

if [[ -e "${VENV_PATH}" && ! -d "${VENV_PATH}" ]]; then
  echo "ERROR: VENV_PATH exists but is not a directory: ${VENV_PATH}" >&2
  exit 1
fi

if [[ ! -d "${VENV_PATH}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_PATH}"
fi

source "${VENV_PATH}/bin/activate"

python -m pip install --upgrade pip wheel setuptools
pip install --index-url "${PYTORCH_INDEX_URL}" torch torchvision torchaudio

if [[ -d "${ROCM_PATH}/bin" ]]; then
  export PATH="${ROCM_PATH}/bin:${PATH}"
fi

python - <<'PY'
import sys

import torch

print(f"python={sys.executable}")
print(f"torch={torch.__version__}")
print(f"torch_hip={getattr(torch.version, 'hip', None)}")
print(f"cuda_available={torch.cuda.is_available()}")
print(f"device_count={torch.cuda.device_count()}")

if getattr(torch.version, "hip", None) is None:
    raise SystemExit("ERROR: installed torch is not a ROCm/HIP build")
if not torch.cuda.is_available():
    raise SystemExit("ERROR: torch cannot see a ROCm GPU")
PY

echo "Created ROCm PyTorch environment at: ${VENV_PATH}"
echo "Use it with: sbatch --export=ALL,VENV_PATH=${VENV_PATH} run_comm_check.sbatch"
