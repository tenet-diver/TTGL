#!/bin/sh
# Inspection-only bootstrap. Never install packages, fetch images or run trials.
set -eu

command -v git >/dev/null 2>&1 || { echo 'Git is unavailable; stop without installing it.' >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo 'Python 3 is unavailable; stop without installing it.' >&2; exit 1; }
TTGL_REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$TTGL_REPO_ROOT"
test -f docs/security/dependency-security-policy.md
test -f tools/usage-monitor/experiments/test_security_gate.py

python3 - <<'PY'
import datetime, importlib.metadata, json, os, pathlib, shutil, subprocess
root = pathlib.Path('work/cloud-setup')
root.mkdir(parents=True, exist_ok=True)
root.chmod(0o700)
versions = {}
for package in ['headroom-ai', 'litellm']:
    try:
        versions[package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        versions[package] = None
report = {
    'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'phase': 'inspection-only',
    'existing_tools_present': {name: shutil.which(name) is not None for name in ['python3', 'git', 'docker', 'codex', 'osv-scanner', 'npm']},
    'package_metadata_only': versions,
    'third_party_packages_imported': False,
    'installed_or_downloaded_anything': False,
    'model_calls_started': False,
    'experiments_authorized': False,
    'tests_passed': False,
    'note': 'Presence is not security approval or evidence that Docker/authentication works. Additional software and runtime images require independent fresh review.'
}
path = root/'setup-report.json'
path.write_text(json.dumps(report, indent=2))
path.chmod(0o600)
print('Inspection recorded. No installation, credential inspection or model calls.')
PY

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/usage-monitor/langfuse -p 'test_*.py'

python3 - <<'PY'
import json, pathlib
path = pathlib.Path('work/cloud-setup/setup-report.json')
report = json.loads(path.read_text())
report['tests_passed'] = True
path.write_text(json.dumps(report, indent=2))
print('Setup checks passed; experiments remain gated. Report: work/cloud-setup/setup-report.json')
PY
