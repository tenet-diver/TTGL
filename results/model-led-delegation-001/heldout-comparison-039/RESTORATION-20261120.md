# Routing holdout restoration, 20 November 2026

All 22 pristine SymPy bases and all 30 reduced-grader files were restored and
verified against the frozen registration. The held-out benchmark still has zero
native calls and zero candidate grades. The 44 new grades are independent empty
and reference controls, with the expected failure and success on every task.
The exact Codex 0.169.0 binary and source subscription binding were recovered.
The numerical baseline process passed two model-free operations and all 102
focused software checks passed.

The original actor contains an OpenSSL revision with five newly recorded advisory
matches. A separate actor uses Alpine's signed 3.5.9-r1 packages, verified against
the official index and security database. A data-only overlay added 9.86 MB to
the existing local layers. The original affected actor was left stopped. The
replacement's actual payload hashes, offline actor boundary and Python runtime
imports passed validation. Both controller and worker actor references must
point to this same patched image. [Security review](../../../docs/security/router-heldout-actor-20261120.json)

The 22 pristine archives contain 160,841,590 payload bytes. Each was retained
and read back from the approved loopback SILO endpoint. After retention and
control grading, the SILO volume had about 1.31 GB free and the workspace about
96 GB. Prior artifact sizes imply about 149–150 MB for generation and another
1 MB for independent grades without workers. Sizing 264 invocations at the
largest observed primary artifact and reserving the largest pristine archive
for each of the 22 possible workers brings the figure to about 489 MB. Archive
metadata and atypically large traces can increase storage use.

The exact 440-slot manifest has 242 independent assignments, 88 duplicate
references and 110 infeasible slots. Matched development projects 42.08–42.34
million native tokens and $11.41–$13.52 at the frozen historical token rates,
varying RouteLLM's executor across the two endpoint extremes. The projected
serial model and public-check envelopes total 8.37–8.56 hours. Setup, archive
replay and independent grading add elapsed time. The 24 native standalone
development episodes span 46 minutes. The 35 metered routed development episodes
span 3 hours 24 minutes, with one nearby deadline whose usage remains unknown.
The registered aggregate limits are 484 invocations, 290.4 million observed
tokens and 28.23 hours of assignment envelopes. The frozen policies allow 264
native calls across the manifest including up to one worker on each of the 22
Observatory assignments. Subscription expense and quota impact are unknown.
[Versioned readiness](../../../experiments/model-led-delegation-001/heldout-continuation-readiness-043.json)

## Execution and monitoring

The existing source-disabled registration 039 remains the historical record.
After active-chat clearance for the source account, the private registration
helper seals continuation 043 with identical assignment IDs, snapshot and task
memberships, model and token rates, thresholds and limits. The actor fingerprint
and its reference in the Observatory worker configuration change to the
reviewed revision. The native runner executes one parent assignment at a time.
One local numerical scorer process remains available to that parent. After
generation seals, the runner restores each retained exact candidate and runs
official-parser grading sequentially. The scoring helper reports the matched
comparisons after the grade seal.

From the repository root with the restored private inputs and canonical local
subscription available, the one-owner commands are:

```sh
export PYTHONPATH="$PWD/src"
export PATH="/home/codespace/.codex/packages/standalone/releases/0.169.0-x86_64-unknown-linux-musl/bin:$PATH"
RESTORE=work/security/model-led-delegation-20261118/continuation-001/restoration-20261120
STUDY=work/security/model-led-delegation-20261118/continuation-001/heldout-comparison-continuation-043
CONFIG=experiments/model-led-delegation-001/heldout-comparison-continuation-043.json
python "$RESTORE/register-patched-continuation.py" --enable
python -m ttgl.model_delegation.heldout "$CONFIG" &&
  python "$STUDY/score-heldout-continuation.py"
```

Read-only monitoring of an existing run is separate from admission:

```sh
PYTHONPATH=src python - <<'PY'
from collections import Counter
from pathlib import Path
from ttgl.experience_routing.io import read

p = Path('work/security/model-led-delegation-20261118/continuation-001/heldout-comparison-continuation-043')
claims = p / 'native-claims.jsonl'
results = Counter(read(f)['status'] for f in (p / 'generation').glob('*/completion.json'))
print('native calls claimed', len(claims.read_text().splitlines()) if claims.exists() else 0)
print('terminal slots', dict(results), 'of 440')
for marker in ('source-archive-ready.json', 'heldout-started.json', 'stopped.json',
               'all-generation-sealed.json', 'completion.json', 'heldout-comparison-report.json'):
    print(marker, (p / marker).is_file())
PY
```

A started assignment or an uncertain call requires reconciliation. An existing
owner, claim or model-started receipt must never be repeated by rerunning the
command. The research schedule remains paused.
