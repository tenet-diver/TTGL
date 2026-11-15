# Appendix: setup and observable knowledge exchange

Completed coding results, synthetic mechanism checks and prospective comparisons
are separate. Examples here are retained publications/tool responses, not invented
dialogue or reconstructed reasoning. They illustrate record types; they are not
a representative sample or proof that memory caused a successful edit.

## A. Completed pilot

Two development libraries, SimPy and TinyDB, were crossed with native Codex, a
shared Markdown notebook and official MCP memory, at total capacities 1/2/4/8:
24 assignments, one attempt per cell, in frozen randomized order. Capacity
includes the parent. Codex chooses actual workers; capacity eight used four or
five threads. All coding agents used GPT-6.1 Sol, low reasoning, CLI 0.167.0;
the hosted native backend reported v2. Each team had 30 minutes, 80 shared
terminal calls and a four-million-observed-token threshold. In-flight work and
compaction could exceed the threshold and remain counted. The timer covers live
parent/worker execution and in-agent checks; preparation and independent replay
are separate. One failed parent stream has a passing saved artifact.

The common MCP terminal exposes an offline container with the skeleton, public
documentation and tests. Solvers cannot access references, evaluator records,
credentials, other cells or prior candidate histories. Independent replay submits
implementation files and restores prescribed tests. The declared runtime uses
Python 3.11.18 rather than dataset Python 3.10. SimPy distribution metadata
supplies its specified version without copying implementation. SimPy passes
140 tests; TinyDB passes 200 with one prescribed skip. No hidden-test robustness
is established. Seven cells have complete inference accounting; 17 have lower
bounds. Missing usage remains unknown; cached/reasoning tokens are subsets.

Exact [protocols/amendments](../../../experiments/codex-team-knowledge-001/scaling-pilot-protocol-005.json),
[cells](pilot-cells.csv), [measurements](pilot-results.json) and
[preparation failures](preparation-results.md) accompany the report.

## B. Actual memory contents

These excerpts come from `007-simpy-mcp_memory-4`. They are agent-authored claims;
a recorded test report is distinct from independent verification.

**Coordination.** Entity `simpy-implementation-ownership` assigns the parent
`core.py` and integration, and workers the event, resource and utility modules.
It also records event-processing contracts and scheduler tuple ordering.
Publication does not prove that another worker read the record.

**Behavioral constraint**, in `simpy-utilities`:

> subscribe_at must reject processed events (callbacks is None), but allow
> triggered unprocessed timeout events; helper process waits event then interrupts
> captured active_process with (event, value) if still alive.

**Claimed check**:

> Verified after core/events integration: `PYTHONPATH=src:$PYTHONPATH python3 -m pytest -p no:cacheprovider -q tests/test_util.py tests/test_rt.py tests/test_version.py` -> 30 passed in 1.78s.

That observation also reports a utility doctest command with no output and exit
zero. This excerpt alone neither verifies the report nor proves reuse.

**Unsuccessful check**:

> Docs verification: pytest docs collection fails before tests because docs/conftest.py imports absent private `_pytest.assertion.util._diff_text`; no harness changes made.

The records contain ownership, assumptions, procedures, reported results and
environment caveats. [Selected full texts and provenance](appendix-evidence-001.json)
include entity names, observation indices, archive/member hashes and the fixed
selection rule. The exporter verifies original archive/member bytes.

**A visible worker report.** In the same assignment, a worker reports completing
queue processing/cancellation, capacity/count properties, priority/preemptive
resources, containers and FIFO/priority/filter stores. It reports 40 resource
tests passing, seven terminal calls and publication under
`resource-event-interface`. The archived terminal records include the resource
test command and its actual outcome, retained separately from the report.
[Exact report and associated tool records](appendix-communications-001.json)
include source/member/item hashes and IDs. This shows observable reporting and
verification activity; it does not establish that the parent read the memory
entity or that the report caused the integrated result.

## C. Empty retrieval and communication limits

An actual completed call in `006-tinydb-mcp_memory-2` returned:

```json
{"tool":"search_nodes","arguments":{"query":"tinydb"},
 "result":{"entities":[],"relations":[]}}
```

Across the pilot, agents published 91 observations; all four read queries returned
no entities. Exact peer-observation retrieval was not observed. Native messages,
inherited context and shared source remained other communication channels.
Some native message payloads are encrypted. We retain metadata and mark content
unavailable; we do not decode or fabricate conversation.

Publication, a completed query, a nonempty hit, exact peer exposure and a checked
subsequent action are distinct observations. Even their temporal sequence does
not alone establish causality. This applies to every later arm.

## D. Separate registered extensions

The [80-cell reserved-library design](reserved-extension.md) remains separate.
At the 11 November inspection, one Cachetools cell passed all 215 tests and the
next IMAPClient cell had started without a completion record; no worker was
visible. The uncertain call is preserved and not automatically repeated.

The user's subsequent request adds tool awareness and existing memory systems.
The [new local registration](../../../experiments/codex-team-knowledge-001/memory-aware-extension-protocol-001.json)
contains **56 planned development assignments**: the same two libraries, seven
arms and capacities 1/2/4/8. These are new policy assignments on reused development
tasks, not held-out validation or replacements for historical outcomes.

| Arm | Shared interface and processing |
| --- | --- |
| Native | Native messages/shared source; common evidence-use guidance |
| Notebook | Shared `KNOWLEDGE.md`, described to parent and children |
| Official MCP memory | Common `repository` entity; explicit read/write examples |
| Mem0 | Stock self-hosted engine; Luna extraction/update; offline BGE |
| Graphiti | Stock engine; Luna extraction; offline BGE, RRF search and reviewed Neo4j derivative |
| Smallville | Pinned author storage/ranking/reflection; Luna importance/reflection; disclosed output compatibility adapter |
| Searchable logs | SQLite FTS5 over observable current-team messages and repository tool inputs/results; no auxiliary LLM |

[Versions and source notices](../../../experiments/codex-team-knowledge-001/memory-aware-extension-versions-001.json)
are recorded separately. Smallville is adapted research code, not the full
simulation. Its reflection threshold is natural, never forced in scored work.
Mem0/Graphiti are self-hosted configurations, not hosted-service results.

Every arm receives common instructions to publish checked findings, retrieve
before dependent work and revalidate stale claims. Tool names, examples and shared
scope appear in the parent prompt and worker-facing instructions. The native
control applies the same discipline through existing channels. Tool-specific
guidance is part of the deployment policy; this is not storage representation
in isolation.

One broker serializes model-based operations across a cell's parent/children.
Stores start empty and are isolated between assignments. Original publications
remain separate from fallible extracted memories and can be read by exact ID.
The log arm indexes allowlisted visible completed messages, native coordination
metadata and repository tool activity. Encrypted/unavailable content remains a
gap. Hidden reasoning, credentials, evaluator records, other assignments and
account-wide historical logs are excluded.

Each team has 30 minutes, 120 terminal calls, a four-million-observed-token
threshold including memory inference and a 128-call maintenance ceiling. All
parent/child/extraction/update/reflection inference, failures and local embedding
work count. Broker queueing is part of run time. Preparation, service startup,
independent replay and research overhead remain separate. No automatic model
retry or repair fallback is permitted.

Before scoring, require untouched reference/skeleton controls, native actor
boundaries, real backend fidelity/isolation, and native parent/child visibility.
Synthetic witnesses establish mechanics, not coding quality.

**Preparation checkpoint:** restored references and skeleton controls pass their
expected gates, as do local embeddings. Smallville/Luna, Mem0/Luna and
Graphiti/Luna pass actual two-client backend checks; searchable logs also pass.
The first Mem0 check fails on its current search-scoping API after completed
model calls. That failure is preserved; a separately recorded `filters` adapter
correction passes. Native reciprocal publication/retrieval checks pass for all
four new arms. Graphiti's fact-only interface first fails to recover an opaque
witness from an episode with zero extracted edges; the separate combined-RRF
interface exposes original episodes and passes. Smallville also needs an explicit
empty-store guard before upstream ranking. Those failed preparations remain in
the record. The 56-cell coding queue's current/final state is in the separate
results report. The
Luna transport canary uses 8,874 tokens, Smallville's backend check
18,159, and Graphiti's 74,783, reconciled against captured usage. These are
research overhead, not coding results or savings. Additional preparation
inference is not included in those three figures.

[Mechanism examples](appendix-mechanisms-001.json) retain versioned outcomes and
parent/child tool sequences with source hashes. These are synthetic diagnostics,
not additional coding subjects. Twenty-three focused software checks pass,
including source-only grading and token-accounting guards. Fourteen independent
gate receipts are frozen before scored inference. Mem0 and Graphiti native
diagnostics also include interrupted transports whose additional inference usage
is unknown; known response totals are lower bounds in those cases.

The accrued spawned-preparation ledger records at least **1,618,481 native tokens**
across 11 audited preflight process groups, with four unknown-usage transport
receipts. This includes failed candidates. Parent implementation/supervision,
local compute and other research costs are additional; total research cost and
cash expense are unknown. No net research saving is claimed.

[Current coding progress](memory-aware-results.md) is published separately from
these preparation measurements and from the original pilot. It remains interim
until every registered assignment has ended or an explicit stop is reported.

**First actual searchable-log coding cell.** SimPy at offered capacity eight uses
four actual coding threads and passes all 140 restored tests with clean artifact
checks. There are 24 completed memory calls: 12 publications and 12 nonempty
searches. Eleven searches return at least one record attributable to a different
native thread through publication provenance or native log-author metadata.
There are no `read_record` calls: exposure occurs through bounded search previews,
not full original-record retrieval. This is observable peer exposure, not proof
of useful integration or an advantage over a matched control. The run takes
190.7 seconds and has at least 2,354,362 native tokens; three interrupted request
receipts leave total inference unknown. Its Standard-rate scenario is at least
16.84702 credits, not actual cash expense. The full matrix continues unchanged.
The source-linked exposure audit and its interpretation remain separate from raw
quality/usage measurements.

**First Mem0 coding cell.** SimPy at capacity four passes all 140 restored tests.
Its 28 memory calls include 12 publications, seven nonempty searches and five
original-record reads, four attributable to peers. Thirteen Luna maintenance
sessions contribute 248,383 native tokens. The shared observed-token threshold
stops the parent at 4,025,626 known team-plus-maintenance tokens, after 482.3
seconds; six interrupted transports leave additional usage unknown. This is a
passing sealed implementation with a budget-stopped parent, not normal final
completion. No retry or replacement occurs.

**First Smallville coding cell.** TinyDB at capacity four passes 200 prescribed
tests with one skip and a normally completed parent. Eleven event observations
are stored; all 11 recorded model calls assign importance through Luna. Six
retrievals occur, and three full original-record reads are attributable to peers.
The natural reflection threshold is never reached: no thoughts are generated
and reflection is not forced. This distinguishes raw observation creation,
Luna importance scoring and possible later reflection. Known total inference is
2,808,438 native tokens, including 99,349 Luna tokens; three interrupted transport
receipts leave the total unknown. These single cells are development examples,
not evidence that either system improves matched accuracy, time or cost.

Examples from subsequent runs must cite actual assignment/tool IDs and source
hashes, retaining empty searches, stale/contradictory findings, failures and
unsuccessful coding attempts alongside useful exposure. Hypothetical dialogue
must never be presented as an observed run.

**Actual Graphiti/Luna coding memory.** The first scored Graphiti cell is TinyDB
at capacity1. Its first retained episode says:

> Exact baseline command python3 -m pytest -p no:cacheprovider -q tests/ exits 4 importing utils.FrozenDict: NameError _immutable undefined; no tests run.

It explicitly retains: “No peer findings returned by search. Uncertainty: hidden
cases unverified; no implementation or test success yet.” That episode has zero
associated entity edges in the retained export; episodic storage and extracted
facts therefore remain distinct evidence. A later retained fact says:

> TinyDB's MyPy hook was syntax checked, but MyPy integration could not be verified because the MyPy package was unavailable.

These are actual agent/model-authored claims, not independent checks of the
baseline or MyPy. Capacity1 does not demonstrate peer learning. The
[reviewed excerpts and source hashes](appendix-graphiti-001.json) identify the
first episode/factual edge in the first scored Graphiti export. This is an
illustrative post-hoc selection, not representative sampling or proof of useful
retrieval. The separately restored final prescribed tests pass.

## E. Reproduction and restricted evidence

**Retained unsuccessful source artifact.** In assignment32, TinyDB/Mem0/Luna at
capacity eight stops at the observed token threshold. Independent source-only
replay records199 passes, one failure and one prescribed skip. The failure is:

```text
FAILED tests/test_storages.py::test_read_once - assert 2 == 3
```

The test expects three storage reads at that point and observes two. The source
and original failing grade are retained without repair, replacement or another
model attempt. This is the first failed replay in registered execution order,
an illustrative negative example. The [sealed excerpt and provenance](appendix-failure-001.json)
include archive/member hashes, the token stop and usage qualifications. Its
completed provider responses absent from native transcripts are explicitly
single-witness measurements; incomplete usage remains unknown.

Relevant files in `tools/usage-monitor/experiments/` are `team_memory_store.py`,
`team_memory_service.py`, `team_memory_backends.py`,
`codex_team_memory_extension.py`, `probe_team_memory_backends.py`,
`probe_team_memory_native.py`, `audit_team_memory_usage.py`,
`export_team_memory_appendix.py` and `test_team_memory_extension.py`.

The [nine-wheel task-runtime lock](../../../experiments/codex-team-knowledge-001/memory-aware-task-runtime-001.lock)
pins exact artifacts. Restore the documented SimPy distribution metadata without
copying implementation; omit the reviewed coverage startup `.pth`. Model-based
memory runtimes remain separate where their dependency graphs conflict.
`team_memory_service.py serve --config ...` starts an explicitly configured
broker; each native worker receives a stdio `mcp` client pointing to the same
socket. Native homes/stores are fresh per assignment. No service command installs
dependencies, downloads a model or starts Neo4j implicitly.

Offline software/exposure checks are:

```sh
python3 -m unittest discover -s tools/usage-monitor/experiments -p test_team_memory_extension.py
python3 -m unittest discover -s tools/usage-monitor/experiments -p test_team_memory_trace.py
```

With reviewed runtimes, an explicitly running capture service and scoped Neo4j,
`probe_team_memory_backends.py` exercises two real clients and
`probe_team_memory_native.py` exercises native parent/child use. Every invocation
requires a fresh output directory. Freeze the environment-specific scoring config
before invoking `codex_team_memory_queue.py` once. The queue never resumes itself.
`analyze_team_memory_extension.py` exports existing measurements without inference;
the attached completion publisher exports the exact queue's final/stop state.

Raw archives/captures remain in ignored `work/security/`. Public files include
only reviewed benchmark examples and measurements. Restricted evidence is needed
to regenerate excerpts or fully audit captures; the public package does not
claim complete raw coverage. Follow the dependency-security policy before new
installation/execution. Commands never implicitly install dependencies, resume
uncertain assignments or enable schedules. Research schedules remain paused.

## F. Interpreting admission failures and provider changes

**Cognee.** The issue was serious enough to block the reviewed installation:
the required Transformers4.57.6 version has four High and one Moderate distinct
GHSA matches in the current recheck, including code-execution and arbitrary-write
classes. Aliased PYSEC records are not counted as additional vulnerabilities.
The [sanitized admission record](cognee-admission-summary-001.json) links exact
advisories and upstream fixes. These findings concern particular loading,
training or serialization paths; their reachability through this selected
Cognee/MCP configuration was not established, and no exploit or coding-quality
experiment was run. This is a dependency-admission decision, not a claim that
Cognee itself was compromised or that every Cognee deployment is unusable.
The reviewed compatible graph could not simply take the patched Transformers
major version because of its Hugging Face Hub constraint.

**Why Luna for Graphiti.** The local Qwen configuration had failed provider
compatibility and exact-fidelity checks; those failures say nothing about a
Luna-backed configuration. The separately registered extension does use Luna
for Graphiti extraction, with actual backend and parent/child gates before
coding. Its scored results are in the extension table, not retroactively added
to the older24-cell pilot. Smallville uses Luna for importance and naturally
triggered reflection; preserving a raw observation is not itself a model rewrite.
Reflection counts must come from actual calls, not the existence of the feature.

**Later runtime security amendment.** Additional native SBOM checks identify
Pillow-bundled libjpeg-turbo3.2.0 and OpenJPEG2.5.4 findings after cell12. The
original runtime and those12 results are preserved. The later text-only
FastEmbed derivative excludes Pillow and image APIs, with unchanged text source
and exact recorded-vector witnesses. No vulnerable plotting/Pillow build
candidate is executed. Pre-model container/log preparation failures remain
separate from coding trials and their model usage is zero only where absence of
process/turn intents, owned rollouts and maintenance intents was verified.
