#!/bin/bash
# Serve the LLM with vLLM on one H100 and run the category pre-labeller against it.
#
#   sbatch scripts/llm/prelabel.sbatch                 # all queued units
#   sbatch --export=ALL,LIMIT=20 scripts/llm/prelabel.sbatch   # trial run
#
# Prerequisites: scripts/llm/download_model.sh and scripts/llm/setup_vllm.sh.
#SBATCH --account=def-mageed_gpu
#SBATCH --gpus=h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --job-name=prelabel
#SBATCH --output=logs/%x-%j.out
set -euo pipefail

MODEL_NAME=${MODEL_NAME:-Qwen3-Coder-30B-A3B-Instruct}
MODEL_DIR=${MODEL_DIR:-$SCRATCH/hf_models/$MODEL_NAME}
PORT=${PORT:-8000}
LIMIT=${LIMIT:-}

module load StdEnv/2023 gcc/12.3 cuda/12.9 python/3.11 opencv/4.13.0 arrow
export HF_HUB_OFFLINE=1

cd "$SLURM_SUBMIT_DIR"
"$SCRATCH/vllm-venv/bin/vllm" serve "$MODEL_DIR" --served-model-name "$MODEL_NAME" \
    --host 127.0.0.1 --port "$PORT" --max-model-len 8192 --gpu-memory-utilization 0.90 \
    > "logs/vllm-$SLURM_JOB_ID.log" 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT

for _ in $(seq 1 90); do  # model load takes a few minutes
    curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null && break
    kill -0 $SERVER 2>/dev/null || { echo "vLLM exited; see logs/vllm-$SLURM_JOB_ID.log"; exit 1; }
    sleep 10
done
curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null || { echo "vLLM did not start in 15 min"; exit 1; }

echo "model: $(cat "$MODEL_DIR/REVISION" 2>/dev/null || echo "$MODEL_NAME")"
.venv/bin/python -m gapstudy.prelabel --base-url "http://127.0.0.1:$PORT/v1" --model "$MODEL_NAME" ${LIMIT:+--limit "$LIMIT"}
