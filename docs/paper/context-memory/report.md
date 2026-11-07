# Context and persistent memory for coding agents: an instrumented development study

**Status:** living scientific-format report, 7 November 2026. Long-horizon public
benchmark and held-out comparisons are pending. Author and affiliation to be supplied.

## Abstract

We study whether context handling and persistent memory reduce complete-task
model inference while retaining coding-agent performance. We reuse a local
authenticated Codex client and existing TTGL/Langfuse instrumentation, separating
native model counters from retained bytes, runtime and subscription expense.
Two new development blocks comprise six source-investigation runs and 24 coding
runs over two three-stage generated projects. Independent-read batching reduces
pooled native tokens from 308,046 to 265,627 (13.77%), with all exact checks passing.
In the chronological diagnostic, full prior-episode history uses 541,910 tokens
versus 656,584 without external memory (17.47% fewer); all six milestones pass in
both conditions. Agent-written notes and optional searchable history show little
aggregate difference, and the search tool is never queried. Every trial's native
counters and unique generation identities reconcile with both CLI summaries and
Langfuse. These small, unreplicated development results nominate candidates;
they do not establish causal memory benefits, statistical noninferiority,
long-horizon transfer, cash savings or an optimal system. A separate adapted
Mem0 setup demonstrates metered extraction, persistence, retrieval and tenant
separation, with integration failures and missing optional components preserved.

**Keywords:** coding agents; context compression; persistent memory; inference
accounting; chronological evaluation; reproducibility.

## 1. Research questions

1. Can context representation or tool-use policy reduce complete-task model
   inference without losing independently verified task success?
2. When tasks revisit a codebase, does persistent knowledge reduce rediscovery
   enough to pay for creation, storage, retrieval, verification and integration?
3. Do maintained memory frameworks improve on full history, ordinary searchable
   files and a simple SQLite FTS control under matched information and budgets?
4. Do selected configurations transfer to fresh long-horizon coding and terminal
   tasks, rather than merely improving constructed retrieval exercises?

The requested engineering outcome is the best supported configuration among
tested candidates. Universal optimality is neither identifiable from a finite
portfolio nor an assumption of this study. Quality retention is an empirical
constraint; a smaller token total cannot compensate for an undisclosed failure.

## 2. Related systems and benchmark selection

Headroom supplies an already-reviewed, pinned lossless transform module. TTGL
uses that subset rather than installing its complete dependency stack. An earlier
four-run generated coding trial observed 10.075% fewer pooled native tokens and
no speedup; its task design and historical installation state limit transfer.
The [original report](../../../tools/usage-monitor/studies/live-harness-results-001.md)
remains authoritative. Capture/compression is currently opt-in after a later
startup recovery; historical default-installation claims do not describe the
present global configuration.

[Mem0](https://github.com/mem0ai/mem0) provides a maintained extraction/storage/
retrieval engine. Its documented deployment permits configurable inference and
storage backends. This study's candidate uses its actual engine with an explicitly
adapted local-Codex transport and pinned local embedding files. It is not the
hosted service or a replication of vendor benchmark claims. Letta and Graphiti
are discovery-stage alternatives; replacing the entire agent with a stateful
agent framework must be distinguished from changing memory alone.

[SWE-bench](https://www.swebench.com/SWE-bench/faq/) evaluates issue resolution,
while [Terminal-Bench](https://github.com/harbor-framework/terminal-bench)
provides executable terminal tasks. Neither ordinary independent-task setup
automatically tests chronological memory reuse. Any extension sharing earlier
episodes must define task order, repository applicability and leakage boundaries;
it must not be presented as an unchanged official score.

[Terminal-Bench Challenges](https://www.tbench.ai/news/terminal-bench-challenges)
explicitly targets long-running project construction and provides programmatic
verification. It is a candidate for within-task context management; its much
larger task scale requires separate environment/resource and security validation.
No Challenge has been started in this study.

[LongMemEval](https://github.com/xiaowu0162/LongMemEval) and
[LongMemEval-V2](https://github.com/xiaowu0162/LongMemEval-V2) offer complementary
memory tests. V2 uses histories of agent trajectories and includes workflow
knowledge and environment-specific pitfalls. Such answer/retrieval evaluations
can measure knowledge retention, but do not by themselves establish successful
code editing. Its released reader/model settings differ from this local Codex
setup; an adaptation would be named and reported separately.

## 3. Methods

### 3.1 Execution and instrumentation

The new trials use Codex CLI 0.167.0, the existing supported ChatGPT login,
`gpt-6.1-sol` and the built-in OpenAI provider. The chronological block explicitly
sets low reasoning effort. No separate API billing, managed memory subscription
or scheduled inference is provisioned. Model invocations use isolated working
directories, frozen protocol/source hashes, recorded commands and durable
per-attempt stdout, stderr and completion artifacts. Process retries are zero.
Built-in transport retry defaults remain; zero process retries is not a claim
of zero provider retries.

Each fresh session has one CLI completion summary. We reconcile its input,
cached-input and output counters against deduplicated native generation events,
then compare exact hashed generation IDs and counter buckets with Langfuse v2.
The initial legacy session/trace API reads returned 404 and were preserved.
The installed v2 observations API returns the records when explicit usage fields
are requested; this was an API mismatch, not evidence of missing inference.

The live exporter preserves immutable delivery receipts. Publication attaches
experiment/task metadata to existing native rows; it does not insert duplicate
generation observations. Transcript and proxy records are separate sources.
These control trials use native transcripts, not claimed proxy coverage.

### 3.2 Independent-read batching

The [frozen protocol](../../../tools/usage-monitor/studies/independent-read-batching-protocol-001.json)
contains three fresh public-source investigations. Each has a neutral control
and a general instruction to batch genuinely independent reads while preserving
results/status and keeping dependent discovery sequential. Order alternates.
Both conditions inspect the same frozen source snapshot. Answers require exact
registered JSON fields; sources must remain unchanged.

The development gate requires all six exact checks, at least 5% pooled token
reduction and at least two pair wins. It is a source-investigation diagnostic,
not a coding benchmark. It does not revisit or replace the earlier rejected
discover-then-read trial.

### 3.3 Chronological memory diagnostic

The [registered corrected block](../../../tools/usage-monitor/studies/chronological-memory-protocol-002.json)
contains two generated Python projects: an event ledger and a build dependency
graph. Each evolves through three feature milestones. All current requirements
are available without memory. Prior code and visible regression tests remain in
the worktree; the next milestone starts a fresh Codex session.

| Condition | Prior information outside evolving source/tests |
|---|---|
| None | No external episode history; identical retrieval interface returns no records |
| Raw history | All earlier visible episodes injected verbatim: task, answer, before/after code and CLI agent events |
| FTS availability | Same episode representation available through SQLite FTS5/BM25; agent chooses whether to query |
| Notes | Earlier agent final notes injected; note generation is included in every arm's task inference |

The search control returns exact nonoverlapping 3,000-character chunks, normally
three hits, with at most 12,000 characters per query. It is deliberately a simple
baseline, not a custom replacement for Mem0. No summary model or embedding call
is hidden in it. Raw and notes injection differ from agent-selected retrieval;
they are not interchangeable treatments.

Every arm follows its own earlier implementation/trajectory, exposing possible
error propagation. This is a longitudinal system diagnostic, not a fixed-corpus
isolation of retrieval quality. A later same-corpus study is required to separate
memory representation from trajectory differences. Condition order rotates
between projects; one replication per sequence/condition leaves substantial
model and order uncertainty.

Visible suites, separate operator checks and input-integrity checks grade every
milestone. Six empty controls fail as expected; all six independent reference
implementations pass visible and operator checks before inference. Three FTS
contract tests cover empty history, exact evidence, query escaping and output
budgets. Operator grades, reference code and future prompts never enter memory.
Directory restrictions combine prompt/sandbox constraints; no cryptographic or
unmounted actor-isolation claim is made for this generated diagnostic.

The development nomination gate requires no lost milestone against None, at
least 10% pooled reduction and a win on both sequences. It is not a statistical
noninferiority test. Existing reserved routing validation cases remain untouched.

### 3.4 Mem0 mechanism preflight and security

The candidate pins Mem0 2.2.1 and FastEmbed 0.9.1 with a 50-package graph. All
50 exact OSV queries returned no matches on 7 November; wheel hashes match the
resolution, and no wheel has a `.pth` file or installer script. Installation is
limited to the private experiment target. A dated receipt records incomplete
base-OS/native-library/publisher/provenance evidence under the user's explicit
Codespace allowance. This is not a security clearance. Known findings would
still block execution. The older vulnerable RTK candidate remains blocked.

The MIT Qdrant BGE-small ONNX port is pinned to commit
`aa8f8b060edb00e03bfdd08813a2949946c8ba55`; model/data hashes are checked before
loading. Downloads and telemetry are disabled. The 384-dimensional local
embedding runtime is measured separately from native Codex inference.

Mem0's standard extraction prompts, engine, Qdrant storage and search are used.
Two process-local factory adaptations supply supported local Codex login and
exact local FastEmbed files. This avoids inventing another memory engine, but
must be disclosed rather than labeled default Mem0/OpenAI-API behavior.
Optional spaCy and BM25 assets were unavailable; the tested configuration falls
back to semantic retrieval without those features. Full-feature setup remains
a separate gate. No mock embeddings are used for efficacy.

### 3.5 Outcomes, costs and uncertainty

Primary outcomes are independently verified task/sequence success and complete
sequence native input plus output tokens. Cached input is a subset counted once;
fresh input and output are reported separately. Memory extraction, summarization,
retrieval calls, retries and integration count whenever used. Local embedding
inferences, CPU runtime and model-loading overhead remain explicit separate
measurements; their token-equivalent or cash cost is unknown.

Elapsed process time includes orchestration; native finite tool runtime and
background service lifetime are different quantities. Parent and child durations
can overlap and must not be summed into task latency. Token-rate scenarios,
subscription charges, quota effects and full deployment cost are distinct.

No confidence interval from this two-sequence diagnostic can establish broad
quality retention. We report every registered cell, including adverse outcomes
and setup failures. Selection uses development evidence only; held-out work
requires a separate frozen protocol and no outcome-driven stopping.

## 4. Results

### 4.1 Independent reads

| Investigation | Neutral tokens | Batching tokens | Exact checks |
|---|---:|---:|---|
| Compression and supervisor | 127,487 | 101,901 | Both pass |
| Capture and polling | 79,444 | 87,439 | Both pass |
| Compression contract | 101,115 | 76,287 | Both pass |
| **Total** | **308,046** | **265,627** | **6/6 pass** |

Batching uses 13.7703% fewer pooled native tokens and wins two of three pairs,
passing its development gate. The losing pair is retained. All six sessions'
unique generation IDs and usage reconcile with Langfuse; combined trial expense
is 573,673 native tokens. The result does not imply the same reduction in cash
or general coding tasks.

### 4.2 Chronological coding

| Condition | Event ledger tokens | Build graph tokens | Total tokens | Change vs None | Milestones passed | Summed process seconds |
|---|---:|---:|---:|---:|---:|---:|
| None | 293,348 | 363,236 | 656,584 | Reference | 6/6 | 179.017 |
| Raw history | 244,886 | 297,024 | 541,910 | −17.4652% | 6/6 | 151.815 |
| FTS availability | 314,195 | 336,001 | 650,196 | −0.9729% | 6/6 | 173.844 |
| Agent notes | 288,263 | 364,645 | 652,908 | −0.5599% | 6/6 | 178.884 |

All 24 milestones pass the registered checks, and all 24 sessions reconcile
exactly between CLI/native counters and Langfuse generation IDs/usage. Raw
history passes the development nomination gate and has lower tokens on both
sequences. Its observed process-time difference is not a demonstrated general
speedup or provider-latency effect.

**The retrieval interface was never queried: zero FTS calls across all arms.**
The FTS row therefore tests offering searchable memory, not successful retrieval
or a memory-system efficiency benefit. Notes show no meaningful supported
improvement in this sample. Later tasks must provide enough rediscovery demand
to test voluntary retrieval without task-specific forced calls.

Stage one contains no prior episode in any condition, yet its usage varies.
For example, build-graph stage one uses 128,046 tokens in None and 80,792 in Raw
history despite no injected history in either. Thus part of the pooled
difference arises before memory can have an effect. The nomination gate was
predefined, but passing it does not identify a causal 17.47% memory benefit.
Fresh replication and a same-information control are necessary.

### 4.3 Preserved integration failures and Mem0 setup

Chronological block001 fails during CLI configuration loading because built-in
provider IDs cannot be overridden. No model thread was created; its exact error
and source are preserved. A new block002 removes those unsupported overrides
under a registered amendment. No completed or uncertain model call is repeated.

The separate Mem0 preflight completes one extraction, consuming 32,935 native
tokens (32,855 input including 12,288 cached; 80 output). Two facts persist.
The initial search rejects an obsolete top-level tenant parameter. After
inspection, corrected read-only queries against the existing store return both
facts for the owning tenant and none for another tenant, with zero additional
LLM calls. The failed call and missing optional components remain recorded.
This is a mechanism result, not task accuracy, economic benefit or a completed
Mem0 comparison against the controls.

### 4.4 Analyst and research expense

An on-demand local Codex analyst reviews a frozen 74-tool-event snapshot and
publishes in TTGL. It distinguishes finite experiment orchestration from model
latency, flags two workspace-root search errors, and recommends scoped evidence
retrieval and nonoverlapping accounting. Its 178,274 native tokens are research
expense, excluded from the reviewed snapshot and included separately here.

At **2026-11-07 15:56:53 UTC**, while implementation remains active:

| Component | Accrued native tokens |
|---|---:|
| Implementation and supervision, current research turn | 10,624,648 |
| Thirty completed trial cells | 3,075,271 |
| Analyst review | 178,274 |
| Mem0 mechanism extraction | 32,935 |
| **Current cumulative lower bound** | **13,911,128** |

The snapshot deduplicates 208 native response identities. Five local embedding
inferences in Mem0 operations are recorded separately; the earlier three-input
embedding setup check is an additional three local inferences. The active
parent makes this a lower bound, not a final project total. Earlier research
programs are excluded. Alternative accounting snapshots must not be added.
The research has no demonstrated net first-use saving, and no cash ROI is
calculated from token counts.

## 5. Discussion

Two findings guide the next work. First, modest control over independent reads
can reduce round trips in source investigation, while the earlier blanket
discover-first instruction made its registered trial worse. Tool-use guidance
requires task-level evaluation rather than inference from shorter outputs.
Second, preserving more prior evidence can coexist with lower aggregate task
tokens, but this diagnostic cannot isolate the benefit from stochastic behavior,
initial-stage differences and path-dependent implementations.

No result yet supports selecting Mem0, Letta, Graphiti or a learned compressor
as the production optimum. The useful outcome of the preflight is a compatible,
metered integration path and documented failure modes. A comparison must count
all extraction/embedding/search costs and include simple full-history/file-search
controls, rather than crediting a framework with exclusive access to knowledge.

## 6. Remaining experiments and completion criteria

The authoritative [progress register](../../research/context-memory-experiment-progress.md)
lists every planned technique and current status. Outstanding work includes
fresh Headroom transfer; actual older-observation masking/recovery; hierarchical
context; maintained memory alternatives; principles/stage/graph ablations;
local/learned compression; cache-aware layout; long-horizon repository and
terminal tasks; and a separately registered held-out comparison.

Completion requires eligible integrations or verified blockers, actual matched
trials under frozen allocations, independent outcomes, reconciled inference
including memory overhead, uncertainty analysis, preserved adverse results,
reproducible artifact hashes and a final manuscript. A config switch or an
offline oracle diagnostic is not a completed live experiment. A candidate is
adopted only within the performance/cost envelope supported by the evidence.

## 7. Reproduction and availability

Public task definitions, operator reference controls and the runner are in
`tools/usage-monitor/experiments/longitudinal_memory_trial.py` and adjacent
modules. Protocols and aggregate measurements are in
`tools/usage-monitor/studies/`. Fresh execution uses a new output directory;
the runner refuses to repeat a started block. Original private attempts must
not be overwritten or silently resumed. Reference controls are outside model
work directories; raw private logs and credentials are not published.

```sh
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_memory_retrieval.py'
python3 tools/usage-monitor/experiments/longitudinal_memory_trial.py prepare work/NEW-REPLICATION --protocol tools/usage-monitor/studies/chronological-memory-protocol-002.json
# A fresh live replication is inference, not a replay of the published attempt:
python3 tools/usage-monitor/experiments/longitudinal_memory_trial.py run work/NEW-REPLICATION
python3 tools/usage-monitor/experiments/longitudinal_memory_trial.py measure work/NEW-REPLICATION
```

Existing Codex authentication and the TTGL native source reader are required.
The commands install nothing. Runtime/version drift can change results; archived
hashes and per-attempt manifests identify the configuration actually tested.
Mem0 setup is private and separately security-gated; the runner's simple controls
do not require it. The scientific report is published only in the TTGL repository;
no journal, arXiv or leaderboard submission is implied.
