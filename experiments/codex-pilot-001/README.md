# Codex conversational feasibility pilot

This directory contains a frozen four-task adapted BugsInPy pilot. The task descriptions, evaluator and model conditions were fixed before model outcomes were available. Protocol amendment removed PySnooper's unrelated `test_disable` feature and clarified the requested custom representation API before workers started.

Models: Luna and Sol; all use medium reasoning and fresh conversations. Arms: Luna only, Sol only, a task-only Luna prompt router, and Luna with up to two conversational Sol expert turns. Each task has a 240-second deadline including routing and expert wait; polling slippage is recorded. Complete token and dollar-cost telemetry is unavailable.

Worker paths: `/workspace/scratch/ttgl-codex-pilot/{luna,sol,precall,personal}/{task_id}`. Each contains `TASK.md` and the same `USER_MEMORY.md`. The Python interpreter is `/workspace/.tools/ttgl-codex-pilot/bin/python` (CPython 3.8.20); dependencies are pinned in `requirements.txt`. These workspaces are copies, without git history. Evaluator and gold material are outside assigned directories, but shared filesystem access remains a soft-isolation limitation.

Restore a fresh clone, including its pinned Python environment, with:

```bash
python scripts/restore_codex_pilot.py --install-env
```

The command requires `uv`, downloads the exact recorded archives, verifies their SHA256 hashes, replays all eight buggy/fixed controls, and only then creates the 16 worker checkouts. It keeps the frozen task selection and protocol unchanged. It refuses to overwrite either existing destination. An incomplete restore retains a diagnostic report; use new destination paths or inspect and remove only that failed restore before retrying. Existing interpreter environments are verified and never silently modified.

`--workspace-root` and `--evaluator-root` support isolated restore validation. The frozen grading script still uses the default `/workspace/scratch/...` paths, so production grading should use the default restore locations. This is a Linux `/workspace` runbook; another directory layout requires a separately documented runner configuration.

Before **each** grade, verify that evaluator source and test trees still match the frozen hashes. Then run grading with the current development Python:

```bash
python scripts/restore_codex_pilot.py --verify-only
python scripts/prepare_codex_pilot.py grade --arm luna --task-id pysnooper-2
```

The separate integrity check is necessary because the frozen grader checks its own code and task registry hashes but does not itself validate every evaluator tree before executing it.

The grader writes JUnit, stdout, a submitted-source diff and `report.json` beneath `grades/<arm>/<task_id>`. A separate output path is required to rerun a grade. `patch_sha256` identifies the canonical sorted changed-file hash manifest; `submission.patch` preserves the readable source diff. The frozen implementation treats **any modification of an existing test file** as an artifact-policy violation, even an additive regression test that leaves old assertions intact. New separate test files are permitted. Record the raw functional test outcome separately from this policy: a submission can pass every executed test and still have `resolved=false` because it changed an existing test file. Do not retrospectively relax or change the frozen grading rule after observing submissions. A later protocol can explicitly permit additive tests, but it is a different experiment. The hidden grader uses published fixed-version tests with unchanged semantics, excluding the unrelated PySnooper feature.

`grader-validation.json` records eight evaluator controls: each unchanged buggy version is rejected, and each official fixed source is accepted. These controls are **not model experiment results**. Two tqdm modules each skip an optional NumPy case; fixed controls and model submissions use the same environment.

The public tasks are small and historically available. This pilot cannot establish frontier software-engineering performance, calibration, cost savings, persistent memory quality, or learning over time. `provenance.json` records all candidates considered, exclusions, archive hashes and interpreter adaptations. No candidate was selected using model outcomes.
