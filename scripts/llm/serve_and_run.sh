#!/bin/bash
# Start vLLM on this GPU node, wait until it answers, run the given command, stop vLLM.
# Used by the Slurm jobs in this folder; the command can use $BASE_URL and $MODEL_NAME.
#
#   serve_and_run.sh <command> [args...]
set -euo pipefail

MODEL_NAME=${MODEL_NAME:-Qwen3-Coder-30B-A3B-Instruct}
MODEL_DIR=${MODEL_DIR:-$SCRATCH/hf_models/$MODEL_NAME}
PORT=${PORT:-8000}
export BASE_URL="http://127.0.0.1:$PORT/v1" MODEL_NAME HF_HUB_OFFLINE=1

module load StdEnv/2023 gcc/12.3 cuda/12.9 python/3.11 opencv/4.13.0 arrow
mkdir -p logs
"$SCRATCH/vllm-venv/bin/vllm" serve "$MODEL_DIR" --served-model-name "$MODEL_NAME" \
    --host 127.0.0.1 --port "$PORT" --max-model-len 16384 --gpu-memory-utilization 0.90 \
    > "logs/vllm-${SLURM_JOB_ID:-local}.log" 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT

for _ in $(seq 1 90); do  # loading the weights takes a few minutes
    curl -sf "$BASE_URL/models" > /dev/null && break
    kill -0 $SERVER 2>/dev/null || { echo "vLLM exited; see logs/vllm-${SLURM_JOB_ID:-local}.log"; exit 1; }
    sleep 10
done
curl -sf "$BASE_URL/models" > /dev/null || { echo "vLLM did not start within 15 minutes"; exit 1; }
echo "serving $(cat "$MODEL_DIR/REVISION" 2>/dev/null || echo "$MODEL_NAME") at $BASE_URL"
"$@"
