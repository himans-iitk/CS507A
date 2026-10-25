#!/bin/bash
# Category pre-labelling (Phase 4) with the open-source LLM on one H100.
#
#   sbatch scripts/llm/prelabel.sbatch                         # all queued units
#   sbatch --export=ALL,LIMIT=20 scripts/llm/prelabel.sbatch   # trial run
#
# Prerequisites: scripts/llm/setup_vllm.sh and scripts/llm/download_model.sh.
#SBATCH --account=def-mageed_gpu
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --job-name=prelabel
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
LIMIT=${LIMIT:-}
scripts/llm/serve_and_run.sh bash -c \
    '.venv/bin/python -m gapstudy.prelabel --base-url "$BASE_URL" --model "$MODEL_NAME" '"${LIMIT:+--limit $LIMIT}"
