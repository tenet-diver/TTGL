# Additional official SWE-bench environment controls

This directory preserves one newly executed official control pair for the frozen
12-task panel. **It contains no model experiment, token metering, or savings
estimate.** The user subsequently requested a handover to another host, so no
further control runs were started. The original `swe-bench-verified-001` artifacts
were not changed.

| Task | Control | FAIL_TO_PASS passing | PASS_TO_PASS passing | Official resolved |
|---|---|---:|---:|---|
| `django__django-13297` | No fix | 0/1 | 52/52 | False |
| `django__django-13297` | Reference patch | 1/1 | 52/52 | True |

Both runs applied their patch successfully, reported no official infrastructure
failure, and exited normally. The full gold log reports 59 tests and `OK`; the
base log reports the expected target error. This pair validates this evaluator
environment. Across the frozen panel, three tasks now have controls: Django and
SymPy are valid; Requests remains invalid for the previously documented fixture
and proxy-sensitive failures. Nine tasks still require controls. No tasks were
removed from the panel.

## Sources and execution

- Official harness commit: `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`, version `5.0.2`.
- Official task repository commit: `3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d`.
- Frozen public manifest: `../swe-bench-verified-001/tasks.json`, SHA-256
  `e6a43141699e22a0dca4f61fac701c677ee4da74fdb13aca81f451b4a4826f58`.
- Image repository digest:
  `swebench/sweb.eval.x86_64.django_1776_django-13297@sha256:1dca304a4ccd9f39df8794fb807c04a4076b5f35aff7d192dc5e0a14f8bf6f43`.
- Exact execution metadata and observed image ID are in
  `django__django-13297.execution.json`; unmodified official reports and complete
  logs are under `logs/evaluation/`.

`runner_versions/initial.py` is the exact runner used for this pair. It invokes
the unmodified official `run_evaluation.main`, using separate fresh containers
for reference and no-fix controls. The no-fix patch adds only `.ttgl_control`;
an empty patch would skip official test execution. A narrow Docker SDK wrapper
adds the managed host's read-only CA bundle and the corresponding Python/pip
trust variables. It preserves Docker proxy defaults and TLS verification.
No evaluator, benchmark tests, or target implementation was changed.

The command executed from the TTGL checkout was:

```bash
/workspace/.tools/ttgl-swebench/bin/python \
  experiments/swe-bench-verified-002-controls/run_controls.py \
  --instance django__django-13297
```

`protocol.json` was saved after the image pull began and before test execution;
it is an environment-control plan, not a preregistered model experiment.
`protocol-amendment-01.json` documents subsequent resource-guard improvements
in the current runner. No additional control was executed with that revision.
The script refuses to overwrite an existing execution record. A new host should
use a new output directory/run prefix rather than overwrite these artifacts.

## Resource limits and continuation

Docker used the `vfs` driver on a 32 GB filesystem. The logical 2.88 GB image
left about 10 GiB free after pulling, and a running evaluator reduced free space
to approximately 4.6 GiB. Runs were sequential. The image was briefly retained
for a separately documented worker preparation smoke check, then removed only
after its owner released it. Cleanup metadata is in the execution record.

`summary.json` records completed and unstarted tasks, report hashes, and combined
panel readiness. `artifact-sha256.json` inventories retained artifacts. A
read-only registry-manifest probe for scikit-learn completed, but its image was
never pulled and neither control was started. There were no partial evaluator
runs or discarded control failures in this continuation.

Regenerate the summary and file inventory with
`python experiments/swe-bench-verified-002-controls/summarize.py`.

On the next host, complete the remaining nine controls and repair the Requests
environment without weakening benchmark tests or network policy. Provide normal
Docker storage and adequate disk (upstream recommends at least 120 GB free), then
verify writable authenticated Codex state and worker dependency/isolation gates
before any scored model run. Carry the full frozen panel, not only the passing
controls, into the readiness record.

**Evaluator-only material:** these logs include reference solutions and hidden
test patches. Never mount this directory, the TTGL checkout, or the private task
distribution into a model worker. Workers receive only fresh upstream base
source and sanitized public task text.
