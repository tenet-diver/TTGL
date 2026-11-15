# Reproducing the memory-aware comparison

The analysis can be regenerated without model calls or new dependencies. Running
the experiment again is a separate, newly registered study. Existing directories
are evidence and must never be treated as retry inputs.

## Evidence and code

The [protocol](../../../experiments/codex-team-knowledge-001/memory-aware-extension-protocol-001.json)
defines 56 assignments: two reused development libraries × seven arms × four
offered capacities. Read the [finalization](../../../experiments/codex-team-knowledge-001/memory-aware-extension-finalized-003.json),
[security amendment](../../../experiments/codex-team-knowledge-001/memory-aware-security-amendment-004.json),
[continuation record](../../../experiments/codex-team-knowledge-001/memory-aware-continuation-finalized-011.json)
and [versions](../../../experiments/codex-team-knowledge-001/memory-aware-extension-versions-001.json)
together. Registration records describe their state when written; later results
do not retroactively change a prospective design into a completed experiment.

The executed harness uses native Codex 0.167.1, Sol low for coding and Luna for
model-based memory work. A loopback capture transport preserves original and
forwarded requests without transformations. Native response IDs deduplicate
usage, and independent SSE receipts reconcile completed responses. Cached input
and reasoning output are subsets, not additional token categories. Interrupted
requests retain unknown usage. The native subscription login does not require
separate API billing; published-rate scenarios are not subscription cash/quota.

Each coding actor has a sealed repository and a shared bounded repository MCP
terminal in a restricted container. Its native filesystem boundary cannot read
the grader, reference sources, credentials or other assignments. A separate
grader restores prescribed tests/resources and replays only implementation
changes in a fresh container. Actor-added notes/tests are excluded; modifications
outside the allowed source scope are flagged. TinyDB's prescribed optional skip
is retained. This is public-test reconstruction, not hidden-test evaluation.

One memory broker serves every parent and child in a cell. Native instructions,
repository AGENTS.md and actual tool schemas describe its scope. Model-created
memories remain fallible; original records are independently pageable. Graphiti
uses combined stock RRF with episodes, Mem0 uses the disclosed dense adapter,
and Smallville uses pinned author code through CompatibleMemoryV4. SQLite FTS5
implements searchable visible logs without a new service. The memory backends,
MCP protocol glue and native transport are separate from the coding policy.

Raw private evidence is ignored under
`work/security/codex-team-memory-extension-20261111/`. `scored-001/` contains
cumulative checkpoints, final/stop receipts, per-cell independent grades,
combined usage audits, immutable XZ archives and archive/recompression hashes.
`preparation-history-013-005-006/` preserves failed pre-model preparation, outside
the scored cell13 directory. Verified pre-model thread-start failures20/21 and uninvoked preparation22 are
preserved under `pre-model-transport-history-008/`; their task turns were never
submitted. Later cells use a120-second wait only for initialize/thread/start,
with original inference transport, prompts and budgets. A later broker bind
failure before the actual cell21 model call is preserved under
`pre-model-service-history-009/`. The prospective socket guard removes only
independently verified dead paths; it leaves active endpoints untouched.
Source quality is conditional on task-model invocation, not flawless first-launch
reliability. Historical 24/80-cell
studies have separate roots.
Cell27's post-generation broker timeout is preserved separately under
`post-generation-shutdown-history-010/`. Its completed source was independently
replayed without a model restart. The exported graph is retained; one unfinished
publication and an unobserved service exit remain incomplete evidence. The
[shutdown amendment](../../../experiments/codex-team-knowledge-001/memory-aware-shutdown-amendment-010.json)
extends only the post-generation wait for cells28–56 and records their exits.
Cell32 retains its original failing grade and token stop. Its audit resumes
after an already-started Luna process ends. The versioned read-only auditor
retains deduplicated positive completed captures missing from native transcripts
as separately labeled single-witness measurements; coverage remains incomplete.
From cell33, a bounded passive drain precedes audit. See
[postprocessing amendment011](../../../experiments/codex-team-knowledge-001/memory-aware-postprocessing-amendment-011.json).
Public JSON/CSV are allowlisted summaries, not replacements for raw evidence.

## Regenerate reports

From the TTGL repository root, with privately retained evidence in its recorded
location:

```sh
python3 tools/usage-monitor/experiments/analyze_team_memory_extension.py \
  --root work/security/codex-team-memory-extension-20261111/scored-001 \
  --protocol experiments/codex-team-knowledge-001/memory-aware-extension-protocol-001.json \
  --output docs/paper/codex-team-knowledge
```

This verifies registered assignment order, sealed grade/audit agreement, positive
completed-response coverage, cross-cell ownership and null unknown totals. It
exports the actual current state; an incomplete matrix remains incomplete.

After all 56 cells end, run the independent final audit:

```sh
python3 tools/usage-monitor/experiments/finalize_team_memory_results.py \
  --root work/security/codex-team-memory-extension-20261111/scored-001 \
  --protocol experiments/codex-team-knowledge-001/memory-aware-extension-protocol-001.json \
  --config work/security/codex-team-memory-extension-20261111/scoring-config-011.json \
  --output docs/paper/codex-team-knowledge
```

It checks all frozen source/runtime/gate hashes, every archived member and link,
and exact compressed archive hashes. It computes separate publication, search,
peer-exposure and maintenance-role counts. It launches no model, grader, queue
or service. Original absolute paths in the configuration need a documented
read-only relocation map on another machine; preserve originals and write a new
analysis receipt rather than rewriting frozen provenance.

## Figures and checks

The initial Matplotlib/Pillow wheel candidate is blocked and was not executed.
The figure generator instead uses three pinned pure-Python SVG dependencies in
the [SVG runtime lock](../../../experiments/codex-team-knowledge-001/memory-aware-svg-runtime-002.lock).
Pygal 3.1.3 is LGPL-3.0-or-later; its two dependencies are MIT licensed. Its
upstream repository was maintained and unarchived at review. No managed plan or
free-tier limit applies. No image-conversion extras, Pillow, native packages or
map plugins are installed. Scripts and external figure assets are removed.

After your environment's security review and isolated installation of exactly
those artifacts, set `PYTHONPATH` to that isolated directory, `NO_LXML=1` and
`PYTHONDONTWRITEBYTECODE=1`, then run:

```sh
python3 -S tools/usage-monitor/experiments/plot_team_memory_extension.py \
  --results docs/paper/codex-team-knowledge/memory-aware-results.json \
  --output docs/paper/codex-team-knowledge/figures
```

It requires the complete paired matrix, produces standalone SVGs and a single
self-contained HTML, and records source/data/output hashes. Unknown inference
totals remain minima without invented upper bounds. Private synthetic rendering
fixtures are software checks, not study measurements.

Local software checks need no model calls:

```sh
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_team_memory_*.py'
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_team_official_memory.py'
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_team_startup_transport.py'
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_team_socket_guard.py'
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_team_post_generation_continuation.py'
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_team_post_generation_continuation_v8.py'
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_team_post_generation_wait.py'
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_team_capture_only_usage.py'
```

## Fresh execution elsewhere

Read the [porting prompt](PORTING_PROMPT.md) before copying files. Restore the
pinned source/runtime artifacts as data, perform current dependency/security
checks under the destination policy, and prepare own task controls and native
actor boundaries. Confirm actual backend fidelity, isolation and reciprocal
parent/child access before freezing a new scoring configuration. Model-based
preflight usage and failed attempts are additional research cost.

The text-only FastEmbed security variant preserves text inference source and
eight observed vectors; it is explicitly an adapted dependency artifact. The
Codespace exception for incomplete security evidence is environment-specific,
and confirmed vulnerability findings still block affected candidates. Original
unpatched runtime artifacts, blocked alternatives and failed calls stay in the
evidence record. Nothing here authorizes restarting a queue, changing normal
provider routing, publishing private histories or resuming a schedule.
Restoring the historical affected runtime as evidence does not authorize
installing or executing it.
