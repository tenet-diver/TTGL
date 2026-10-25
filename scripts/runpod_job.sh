#!/usr/bin/env bash
# Run inside an already provisioned GPU workspace. This does not create/delete pods.
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo 'Usage: runpod_job.sh DATASET OUTPUT_DIR CONFIG [--dry-run|--run]' >&2
  exit 2
fi

ttgl_dataset=$1
ttgl_output_dir=$2
ttgl_config=$3
ttgl_mode=${4:---dry-run}
case "$ttgl_mode" in
  --dry-run|--run) ;;
  *) echo 'Mode must be --dry-run or --run.' >&2; exit 2 ;;
esac
[[ -f "$ttgl_dataset" && -f "$ttgl_config" ]] || {
  echo 'Dataset and config files must exist.' >&2
  exit 2
}
if [[ -e "$ttgl_output_dir" ]]; then
  echo 'Use a new output directory; existing runs are preserved.' >&2
  exit 2
fi

export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
if [[ "$ttgl_mode" == '--dry-run' ]]; then
  exec python -m ttgl.train --dataset "$ttgl_dataset" --config "$ttgl_config" \
    --output-dir "$ttgl_output_dir" --dry-run
fi

: "${TTGL_JOB_TIMEOUT_SECONDS:?Set a positive job timeout derived from the approved GPU budget.}"
if [[ ! "$TTGL_JOB_TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]]; then
  echo 'TTGL_JOB_TIMEOUT_SECONDS must be a positive integer.' >&2
  exit 2
fi
command -v timeout >/dev/null
# timeout limits this process, not the billing lifetime of the pod.
exec timeout --signal=TERM --kill-after=30s "$TTGL_JOB_TIMEOUT_SECONDS" \
  python -m ttgl.train --dataset "$ttgl_dataset" --config "$ttgl_config" \
  --output-dir "$ttgl_output_dir" --run
