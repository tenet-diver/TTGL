#!/usr/bin/env bash
set -euo pipefail
cd /workspace/TTGL
ttgl_env=/workspace/.tools/ttgl-research
export UV_CACHE_DIR=/workspace/.cache/uv
if [[ ! -x "$ttgl_env/bin/python" ]]; then
  uv venv --python python3.12 "$ttgl_env"
fi
uv pip install --python "$ttgl_env/bin/python" -r requirements-research.lock
uv pip install --python "$ttgl_env/bin/python" --no-deps -e .
"$ttgl_env/bin/python" -c 'import ttgl, sklearn, numpy; print("TTGL research environment available")'
bash scripts/setup_runpod.sh
