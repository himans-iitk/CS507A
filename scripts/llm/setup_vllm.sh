#!/bin/bash
# Build the vLLM environment on /scratch from the cluster wheelhouse (login node, once).
# vLLM needs OpenCV and Arrow, which this cluster only provides as modules, and the
# venv must use the module's Python so it can see them.
set -euo pipefail
module load StdEnv/2023 gcc/12.3 cuda/12.9 python/3.11 opencv/4.13.0 arrow
virtualenv --no-download "$SCRATCH/vllm-venv"
"$SCRATCH/vllm-venv/bin/pip" install --no-index --upgrade pip
"$SCRATCH/vllm-venv/bin/pip" install --no-index vllm
"$SCRATCH/vllm-venv/bin/python" -c "import vllm, torch; print('vllm', vllm.__version__, 'torch', torch.__version__)"
