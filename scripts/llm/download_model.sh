#!/bin/bash
# Download the open-source LLM's weights to /scratch (run on a LOGIN node: compute nodes have no internet).
# ~61 GB. The revision is pinned so the paper can name the exact weights used.
#
#   bash scripts/llm/download_model.sh
set -euo pipefail

MODEL_ID=${MODEL_ID:-Qwen/Qwen3-Coder-30B-A3B-Instruct}
REVISION=${REVISION:-b2cff646eb4bb1d68355c01b18ae02e7cf42d120}
DEST=${DEST:-$SCRATCH/hf_models/$(basename "$MODEL_ID")}

cd "$(dirname "$0")/../.."
mkdir -p "$DEST"
.venv/bin/hf download "$MODEL_ID" --revision "$REVISION" --local-dir "$DEST"
echo "$MODEL_ID@$REVISION" > "$DEST/REVISION"
du -sh "$DEST"
