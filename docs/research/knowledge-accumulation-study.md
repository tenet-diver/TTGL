# Knowledge accumulation: paper and repository-memory continuation

9 November 2026. Active chat only; research schedules remain paused.

The user requested a Markdown research paper comparing our memory work with
Mem0, Zep/Graphiti, TokenEconomizer, and native memory on/off, emphasizing repeated
work in the same codebase. They also requested a cheap-model challenge graph
that a larger solver can use and edit, retaining useful experience across tasks.

The [working paper](../paper/knowledge-accumulation/paper.md) contains a focused
primary-source literature review, two completed historical diagnostic experiments,
a new zero-model metadata audit, the graph method, limitations, and conclusions.
It explicitly does not claim completed new repository-memory trials or establish
innovation/generalization benefits. Do not overwrite the separate routing paper.

## Completed this continuation

* Audited all 111 VibeMemBench target metadata records and history filenames;
  found 90 repositories and nine Python repositories with multiple targets.
* Reserved cfn-lint's five targets for development and moto's four targets for
  validation using a deterministic metadata-only rule. No validation task text,
  patches, or trajectory content was inspected for tuning. History filenames
  are metadata; strict earlier-ordinal filtering excludes own/future episodes.
* Added 13 passing software checks for metadata and leakage boundaries. One
  initial audit rejected a null license; the corrected schema preserves null
  and excludes that repository from license-eligible selection.
* Inspected the first task's original image as registry data only. Its
  digest-verified Python source member matches 3.10.19 and lacks a documented
  security fix. The image is blocked before installation/execution. Complete
  final-overlay, OS and dependency scanning remains unfinished; do not portray
  this as a complete image audit or claim all benchmark images are affected.
* Rechecked the existing exact Mem0 (50), Graphiti (29), and MCP graph (4)
  package graphs through OSV: no matches on 9 November. This is an advisory
  recheck, not new installation, execution, full OS coverage, or clearance.
* No new model calls, image execution, package installation, global memory/config
  changes, service deletion, or schedule changes occurred.

## Read before executing

The [prospective protocol](../../tools/usage-monitor/studies/repository-memory-protocol-001.json)
is a design and metadata reservation, **not a frozen runnable experiment**.
It lists the missing environment, native-memory, graph-backend, capture, budget,
and source-freeze gates. Its initial development unit is the first two targets;
the remaining three keep their order. Do not start the whole arm matrix blindly.

The upstream VibeMemBench contract resets memory per target and supports only
add/search. Persistent solver edits across live targets are a separately named
online extension. The same-facts graph/flat ablation uses a fixed pre-task
snapshot; divergent live solvers cannot be described as having identical facts.

Native memory needs a real positive generation/injection check in an isolated
store. Latest Codex source has eligibility rules and separate memory endpoints;
the installed binary must be checked. A resumed thread or enabled-but-inactive
flag is not a native durable-memory treatment. Include every background call in
accounting; never read/write the user's normal personal memory for this study.

The benchmark's `install_config.test_cmd` can reveal targeted hidden test paths.
Do not expose raw installation metadata, target patches/test patches, fail/pass
lists, evaluator logs, or current/future trajectories to actors or memory. Fetching
the metadata-viewer JSON also downloads private grading fields: these remain in
the ignored private store, are not forwarded, and are not used to select cases.
Pinned Parquet versus dataset-viewer equivalence still needs verification.

Prefer a patched compatible task environment, reviewed dependency graph, and
empty/reference evaluator controls over running the affected original image.
Do not delete live observability services, volumes, credentials or histories to
make space. Docker's data root is on the nearly full root filesystem; `/tmp`
has substantially more space. Do not switch Docker daemon roots casually.

## Evidence and reproduction

* [Metadata audit](../../tools/usage-monitor/studies/repository-memory-metadata-audit-001.json).
* [First-image preflight](../../tools/usage-monitor/studies/repository-memory-image-preflight-001.json).
* [Completed coding diagnostic](../../tools/usage-monitor/studies/luna-memory-tokeneconomizer-final-results-001.json).
* [Completed Mem0/cache diagnostic](../../tools/usage-monitor/studies/cache-memory-reuse-results-001.json).

Private inspection sources and receipts live in
`work/security/knowledge-generalization-20261109/`; prior frozen model runs remain
under `work/security/context-memory-20261107/`. Do not re-run or replace them.

Run the new checks with:

```bash
python -m unittest discover -s tools/usage-monitor/experiments -p test_repository_memory_design.py
```

The metadata audit accepts only its exact allowlist and history filenames. Its
output must be a new file; it never overwrites an existing reservation:

```bash
python tools/usage-monitor/experiments/repository_memory_design.py \
  --targets work/security/knowledge-generalization-20261109/vibemem-targets-allowlist.json \
  --dataset-metadata work/security/knowledge-generalization-20261109/vibemem-data.json \
  --output /tmp/repository-memory-audit-check.json
```

Compare that result with the committed audit. It makes zero model calls and
executes no downloaded benchmark code. Public receipts and private input hashes
are distinct from a redistributable full dataset or official benchmark score.
