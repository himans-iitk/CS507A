#!/bin/bash
# Score all agent units with the embedding matchers on one GPU.
# Models must already be in $SCRATCH/hf_home (compute nodes have no internet).
#
#   sbatch scripts/detector/embed.sbatch
#SBATCH --account=def-mageed_gpu
#SBATCH --gpus=nvidia_h100_80gb_hbm3_2g.20gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --job-name=embed
#SBATCH --output=logs/%x-%j.out
set -euo pipefail

module load StdEnv/2023 cuda/13.2
export HF_HOME=$SCRATCH/hf_home HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false

cd "$SLURM_SUBMIT_DIR"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
for model in sentence-transformers/all-MiniLM-L6-v2 BAAI/bge-base-en-v1.5 Qwen/Qwen3-Embedding-0.6B; do
    .venv/bin/python -m gapstudy.detector.score --matcher "$model" --device cuda
done
