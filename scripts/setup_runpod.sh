#!/usr/bin/env bash
set -euo pipefail
cd /workspace/TTGL
ttgl_env=/workspace/.tools/ttgl-runpod
export UV_CACHE_DIR=/workspace/.cache/uv
if [[ ! -x "$ttgl_env/bin/python" ]]; then
  uv venv --python python3.12 "$ttgl_env"
fi
uv pip install --python "$ttgl_env/bin/python" -r requirements-runpod.lock
"$ttgl_env/bin/python" -c 'import runpod; assert callable(runpod.get_gpu); print("Runpod SDK available; no cloud request made")'
