# SWE-bench Verified: frozen sample and official evaluator controls

This directory contains a **prepared 12-task sample**, plus actual executions of
the official evaluator's reference and no-fix controls. It contains no new model
benchmark results. The metered conversational experiment remains unexecuted
because this managed host cannot initialize nested Codex sessions.

The sample was selected on 26 October 2026 before model outcomes: rank all 500
Verified instance IDs by `SHA256("ttgl-swe-verified-001:" + instance_id)` and take
the first 12. No tasks were removed after control failures. This is an engineering
sample, not a powered test of a 3-percentage-point noninferiority margin. The
full study should freeze a larger panel before inference.

## Sources and reconstruction

- Official harness: `SWE-bench/SWE-bench`, commit
  `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`, package version `5.0.2`.
- Official standalone task distribution: `SWE-bench/swe-bench-tasks`, commit
  `3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d`.
- Dataset identity: `SWE-bench/SWE-bench_Verified`, test split, exactly 500
  matching task records in that official repository.
- `tasks.json` contains issue text, repository and base revision only. Its
  SHA-256 is `e6a43141699e22a0dca4f61fac701c677ee4da74fdb13aca81f451b4a4826f58`.
- `preparation.json` records selection, archive hashes and per-task file hashes.
  `dataset_revision` in `tasks.json` identifies the official task-repository
  commit, not a Hugging Face commit. Do not silently compare datasets from
  different releases as identical.

The official v5 task loader reconstructs the complete evaluation records from
`task.yaml`, `tests.json`, `eval.sh`, issue text and patches. It does not contact
Hugging Face. This is a documented official distribution, independently available
on GitHub; it is not a workaround to bypass a denied destination. The alternative
Hugging Face parquet download was blocked at its CDN in this runtime.

The harness is MIT licensed. The inspected Verified dataset card and task
repository do not supply a separate explicit dataset license; this document
does not extend the harness license to third-party issue text or code. Source
repository licenses continue to apply to their code. Artifacts here are attributed
research materials, not a claim of ownership over benchmark tasks.

## Reproduce preparation

From the TTGL checkout, with Python 3.12+ and `uv` installed:

```bash
python3.12 scripts/prepare_swe_bench.py \
  --evaluator-root /workspace/scratch/ttgl-swe-evaluator \
  --install-env /workspace/.tools/ttgl-swebench
```

The command verifies SHA-256-pinned source archives, synchronizes the 76
dependencies in `requirements-evaluator.lock`, installs the pinned official
harness, and reconstructs the frozen sample. It was run successfully twice with
identical public manifest hashes. `requirements-evaluator-observed.txt` records
the inspected installation; its local harness path is provenance, not a portable
installation requirement.

The evaluator directory includes reference solutions and tests. Keep it outside
every agent's readable filesystem. The public manifest alone does not enforce
isolation. Published control logs also reveal reference/test patches: mount only
the task checkout and sanitized task text into model workers, not this directory
or the TTGL checkout.

## Run the official evaluator

Use a fresh run ID for each changed prediction, because the official evaluator
caches by run ID and instance ID:

```bash
/workspace/.tools/ttgl-swebench/bin/swebench eval \
  /workspace/scratch/ttgl-swe-evaluator/selected.dataset.json \
  --predictions /path/to/run/predictions/small.jsonl \
  --run-id unique-small-run-id --workers 1 --timeout 600
```

The predictions are ordinary official JSONL rows with `instance_id`,
`model_name_or_path`, and `model_patch`. `--gold` replaces `--predictions` to run
reference patches; `--instance INSTANCE_ID` is repeatable. Omit `--task-repo` for
this prebuilt-image workflow: v5 treats it as a request to build images locally.
The reconstructed local JSON already contains the official evaluation scripts.
Archive image digests, `patch.diff`, `report.json`, `test_output.txt`, and run
metadata. Bind imported grades to the exact prediction hash.

The no-fix controls here add a harmless `.ttgl_control` marker file. An empty
patch would be short-circuited by the evaluator and would not demonstrate that
regression tests actually fail on the base source. No implementation or tests are
changed by the marker patch.

## Executed controls and resource limits

`controls/summary.json` is regenerated from the four official reports by
`python scripts/summarize_swe_controls.py`; full original logs are retained.

| Instance | Control | Regression tests passing | Preservation tests passing | Official resolved |
|---|---|---:|---:|---|
| `psf__requests-5414` | No fix | 0/1 | 123/130 | False |
| `psf__requests-5414` | Reference patch | 1/1 | 123/130 | False |
| `sympy__sympy-17139` | No fix | 0/2 | 67/67 | False |
| `sympy__sympy-17139` | Reference patch | 2/2 | 67/67 | True |

The Requests control is invalid for this environment: its reference patch passes
the bug-specific regression, but seven declared preservation tests fail. The full
test log additionally shows 158 fixture errors involving the absent `httpbin`
fixture plugin. Proxy-sensitive failures also occur. The official harness marks
these as ambiguous failures rather than `infra_failure`; our invalid-control
classification follows the failing reference patch. Neither tests nor inherited
proxy settings were weakened to obtain a passing result.

Only two of the 12 selected tasks received control checks. A successful control
on SymPy establishes that its official evaluator can run here; it does not validate
the other selected tasks or establish model performance.

The upstream recommendation is x86_64, at least 120 GB free disk, 16 GB RAM and
8 CPU cores. This host has a 32 GB filesystem and Docker's `vfs` driver. A single
2.69 GB Requests image used roughly 20 GB with duplicated layers and a running
container. Images were therefore evaluated one at a time and only images created
for these controls were removed afterward. Use an ordinary supported Docker
storage driver and adequate disk on the next host. Keep TLS verification enabled;
networked containers in a managed proxy environment also need the documented
read-only CA mount and tool-specific trust configuration. The official CLI does
not itself install this session's CA into published images.

These controls use no LLM inference, make no claim about token or subscription
savings, and are not additional model trials in the earlier pilot.
