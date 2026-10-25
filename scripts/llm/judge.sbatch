#!/bin/bash
# LLM coverage judgements (Phase 6, "embeddings + LLM") on one H100.
# The candidates come from an embedding matcher's scores file.
#
#   sbatch --export=ALL,SCORES=data/processed/scores/BAAI__bge-base-en-v1.5.csv scripts/llm/judge.sbatch
#   (add LIMIT=20 for a trial run)
#SBATCH --account=def-mageed_gpu
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --job-name=judge
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
: "${SCORES:?set SCORES=data/processed/scores/<matcher>.csv}"
LIMIT=${LIMIT:-}
scripts/llm/serve_and_run.sh bash -c \
    '.venv/bin/python -m gapstudy.detector.llm_judge --scores "'"$SCORES"'" --base-url "$BASE_URL" --model "$MODEL_NAME" '"${LIMIT:+--limit $LIMIT}"
