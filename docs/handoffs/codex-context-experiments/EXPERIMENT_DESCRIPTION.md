# EXPERIMENT_DESCRIPTION: Composable context and memory optimization for Codex

Version 1.0 • 4 November 2026 • Specification, not an implementation

## 1. Purpose and binding scope

Build an experimental harness that launches isolated OpenAI Codex coding sessions on approximately ten real development prompts from the owner's repositories. Determine whether context and memory interventions reduce total cost per successful task without unacceptable correctness or latency regressions. A 20–30% reduction is a research target, not an assumed result or a guaranteed saving.

**Existing observability is already implemented. Reuse its telemetry, traces, token/cost logs, instrumentation, hooks, storage and dashboards. Audit compatibility and add only missing experiment identifiers or transformation events. Do not replace collectors, introduce a parallel billing ledger, or rebuild tracing.** The archive below is an exact-content/recovery layer that references existing traces; it is not a new observability platform.

The only optimization ideas in scope, in binding priority order:

1. Observation masking.
2. Deterministic/semantic tool-output compression.
3. Hierarchical memory / LCM-style compaction.
4. Reversible context compression with exact archive/retrieval.
5. Persistent cross-session memory through self-hosted Mem0.
6. Experience-to-generalizable-principle extraction inspired by ReasoningBank and ACE.
7. Stage-aware memory retrieval.
8. Knowledge graph linking code, episodes and principles.
9. Local lightweight relevance, summarization and selection models.
10. Cache-aware compaction, stable prefixes and billing.

Composability, evaluation, archiving and safety are infrastructure supporting those ten ideas, not extra treatments. Do not add adaptive online policy learning, multi-agent coding, model routing, fine-tuning, a new coding agent or automatic model upgrades. Fixed thresholds and a predeclared cache policy are allowed. Scope extensions require a separate protocol.

### Relationship to the earlier research

The retrieved conversation, “Review LLM Coding Agents,” establishes the Adaptive Context Optimization direction: compare simple masking and deterministic compression with more expensive methods; preserve exact originals; account for cache behavior; measure real repository outcomes; separate within-session context management from cross-session transfer.

Its VISTA-Memory review establishes a hybrid of generalized engineering principles, original supporting trajectories and stage-aware retrieval. It also motivates stock self-hosted Mem0, keyword/raw-history retrieval, memory ingestion costs, procedural-detail retention and a separate memory-dependent task subset. These are carried forward here. VISTA means the owner's VISTA-Memory project, not an unrelated public visual-agent project with the same acronym.

The original attached Adaptive Context Optimization brief and full VISTA study are unavailable in the retrieved material. This specification is grounded in the accessible discussion and the user's explicit requirements; it does not claim to reproduce missing documents, their exact five-condition design, or their empirical results. Before implementation, register any recovered originals in `sources.lock.json`, map discrepancies, and version protocol changes before runs. Work can proceed on the confirmed requirements without inventing missing content.

### Questions and decision rule

Primary: Which eligible configuration lowers pooled cost per successful task relative to its matched baseline? Secondary: Which interventions preserve correctness, what is their overhead, and do principles transfer beyond raw-history retrieval? Causal claims concern the tested harness, tasks, model and authentication route only.

A deployment candidate must pass the engineering/safety gates, achieve observed success no worse than baseline on the pilot, and then meet the confirmatory criteria in §12. A ten-task experiment is a pilot and can select candidates; it cannot establish broad quality equivalence.

## 2. Discovery and compatibility audit: milestone zero

Produce `audit/observability-map.md`, `audit/capabilities.json`, `audit/cost-reconciliation.json` and a redacted sample joined run. Read project instructions before inspecting repositories. Do not extract credentials or modify the user's active Codex setup.

Inventory:

- Existing trace provider, exporters, schema/version, retention, sampling, clocks, retry representation and session identifiers.
- Token and charge source, per-request versus cumulative counters, cached-input meaning, reasoning/output inclusion, cache-write fields, currency, model/date/rate-card versions, missingness and duplicate billing risks.
- Codex binary/version/hash; CLI help; desktop version; model/provider identifier and reasoning settings; auth route; profiles; instructions/skills; tools/MCP definitions; hooks; native compaction settings and automatic behavior.
- Existing archive/raw logs: fidelity, truncation, binary handling, event order, streaming chunks, stdout/stderr separation, permissions and searchable fields. Reuse existing exact blobs when their integrity and retention satisfy §5.
- Ability to observe and actually change each intended surface. Separate diagnostics from context mutation. Verify with harmless canary content and inspect what the next model call actually receives where available.
- CPU, accelerator, RAM, OS, local model runtime, energy measurement availability and shared-load conditions.

Map each required metric to existing field/query, units, authority, availability and validation. Use statuses `available`, `derivable`, `missing`, `unverifiable`; never silently convert missing data to zero. Reconcile a short API-metered run's usage and charge against the provider's available billing evidence. If only token × rate calculations exist, label modeled cost, not exact paid cost. Existing subscription usage logs do not by themselves establish per-request invoice charges.

Minimal additions, only if absent: `experiment_id`, `protocol_hash`, `task_id`, `run_id`, `pair_id`, `variant_id`, `attempt_id`, `replicate_id`, `config_hash`, `repo_commit`, `memory_snapshot`, `auth_route`, `adapter_id`, `treatment_applied`. Attach them to existing spans or a small side manifest keyed by existing IDs. Add transformation/recovery/acceptance/failure records only when existing events cannot express them. Never duplicate provider usage totals in both hook and export paths.

**Audit exit gate:** demonstrate one joined session → requests → tools → usage → final patch → independent acceptance result. Demonstrate baseline identity and one canary intervention; state what cannot be measured or intercepted. Any missing primary outcome or invalid intervention blocks that experimental cell, not all unrelated cells. Request missing repo/task choices only after discovering available context. Budget is required before paid runs; specification preparation requires no paid execution.

## 3. Codex integration and capability boundaries

Use the official CLI as the primary controlled execution surface. Record documentation date and installed-version evidence. Revalidate capabilities during implementation; this document's proposed `ctxexp` commands are a new harness contract, not existing Codex commands.

| Surface | Supported use / audit evidence | Limits and experiment classification |
|---|---|---|
| `codex exec --json` | Noninteractive session launching and emitted JSONL events; documented officially [O1] | Emitted events are not proof of complete wire context, exact invoices or writable history. Reconcile with existing telemetry. |
| Lifecycle hooks | Documented events and version-specific hook feedback [O2] | Pre/PostModelRequest diagnostic output cannot rewrite context. PostToolUse feedback is not a general output-replacement API. Prove specific behavior; do not infer masking from a hook running. |
| Wrapper tools | Tools under harness control can archive then return compressed output | Only wrapped traffic is affected; ordinary shell/file tools can bypass. Measure coverage and preserve tool semantics/exit codes. A shell alias alone cannot guarantee interception. |
| MCP server | Exposes archive/retrieval and optional controlled tool wrappers [O3] | MCP cannot delete arbitrary native conversation history. Retrieval costs context and calls. Equalize tool schemas within a matched comparison. |
| Configurable model-provider gateway / proxy | Candidate API-key route after verifying the installed provider configuration and protocol | Context rewriting is experimental. Streaming, stateful continuations, opaque items and authentication must remain valid. Unsupported subscription routing is excluded. |
| Pinned Codex source modification | Optional explicit research fallback only | Separate experimental stratum with its own unmodified-fork baseline; never label it stock Codex. Do not implement a fork unless other integration routes cannot answer the question and scope is approved. |
| Codex desktop | Manual validation using an independently verified compatible setup | Do not assume CLI flags, hook paths or proxy behavior carry over. Report separately; desktop absence does not block the CLI study. ChatGPT desktop is a different surface. |

Full history masking, hierarchical replacement and prefix re-layout require verified context control. A wrapper that shortens only a new tool result can test idea 2; it cannot establish idea 1 or 3. Retrieval-only Mem0 through MCP can be tested without whole-history rewriting. Mark cells `eligible`, `shadow_only` or `unsupported`, with evidence and affected traffic percentage. Never silently substitute an MCP hint for actual context removal.

For proxy experiments, test request/response streaming, cancellation, retries, tool IDs/order, error statuses, usage, reasoning/opaque item pass-through and provider continuation behavior. Rewriting must not invalidate a previous-response/stateful reference. If context cannot be safely reconstructed without modifying opaque model state, skip the affected treatment. Do not decrypt or rewrite hidden reasoning. Authentication tokens stay outside request archives. The same proxy in byte-preserving mode must be the baseline for rewriting arms; also compare it with native baseline to quantify proxy overhead.

Observe native Codex compaction as a competing mechanism. Keep settings matched and fixed. “Baseline” means normal native behavior, not infinite history. If native compaction cannot be disabled, record its events and exposure; do not claim exclusive compaction effects. Change one surface per comparison. Do not bypass permissions or approvals to make treatment work.

Official documentation supports CLI execution, hook semantics and MCP integration [O1–O3]. It does not establish that all listed experimental interventions are available in every Codex version or desktop subscription session.

## 4. Modular architecture and contracts

Suggested package layout (choose language to fit existing repository; typed interfaces are normative, TypeScript syntax illustrative):

```text
ctxexp/
  adapters/{codex_cli,tool_wrapper,mcp,experimental_proxy}
  plugins/{mask,tool_compress,hierarchy,reversible,mem0,principles,stage,graph,local_model,cache}
  core/{contracts,pipeline,archive,capabilities,budgets,provenance}
  evaluation/{tasks,runner,acceptance,analysis}
  integrations/existing_observability
```

Stages form a validated DAG, not an arbitrary chain of destructive string edits:

```text
existing source → exact archive → classify/protect → tool compression
                                      ↓
             stage signal → candidate retrieval → rank/budget
                                      ↓
          context view → hierarchical summaries → observation masking
                                      ↓
                    reversible references → cache layout → validation → send
completed training episode → extract/curate principles → versioned memory snapshot
```

The archive/protection/validation infrastructure is always available, but must not inject prompts or tools into native baseline. Each of the ten treatments has its own explicit enabled flag. Shared archive access can be used by several ideas; count shared costs once. The reversible *treatment* controls model-visible reference substitution and expansion behavior, separate from passive archival. Local model is a replaceable strategy provider, not a second compressor automatically applied on top of another.

```typescript
type Ref = { blobSha256: string; byteStart: number; byteEnd: number };
type Scope = { owner: string; repo: string; commit: string;
  split: 'train'|'dev'|'test'; memorySnapshot: string };
type Event = Readonly<{ schemaVersion: 1; id: string; sequence: number;
  sourceTraceId: string; runId: string; parentId?: string; time: string;
  kind: 'user'|'assistant'|'tool_call'|'tool_result'|'usage'|'compaction';
  role: string; toolCallId?: string; scope: Scope; original: Ref;
  trust: 'instruction'|'untrusted_data'; contentType: string }>;
type Segment = Readonly<{ id: string; sourceRefs: Ref[]; text: string;
  protectedSpans: Array<{start: number; end: number; reason: string}>;
  representation: 'original'|'extract'|'summary'|'placeholder'|'retrieval';
  transformationIds: string[]; tokenEstimate: number }>;
type View = Readonly<{ revision: string; segments: Segment[];
  tokenBudget: number; recentWindow: string[]; stage: StageSignal }>;
type StageSignal = { stage: 'investigate'|'plan'|'implement'|'test'|'review'|'unknown';
  confidence: number; evidenceEventIds: string[]; classifierVersion: string };
type Transform = { id: string; plugin: string; version: string; configHash: string;
  inputHash: string; outputHash: string; sourceRefs: Ref[];
  elapsedMs: number; usageTraceIds: string[]; omissions: Ref[];
  disposition: 'applied'|'noop'|'fallback'|'rejected'; reason?: string };
type Delta = { expectedRevision: string; replacements: Segment[];
  removedSegmentIds: string[]; transform: Transform };
interface Plugin {
  manifest: { id: string; version: string; phases: string[];
    requiresCapabilities: string[]; before: string[]; after: string[];
    conflicts: string[]; configSchema: object };
  init(services: Readonly<Services>, config: unknown): Promise<void>;
  propose(input: Readonly<View>, event?: Event): Promise<Delta | null>;
  validate(input: Readonly<View>, delta: Delta): Promise<Validation>;
  close(): Promise<void>;
}
interface Archive {
  put(bytes: Uint8Array, metadata: object): Promise<Ref>;
  get(ref: Ref, scope: Scope): Promise<Uint8Array>;
  verify(ref: Ref): Promise<boolean>;
}
interface MemoryAdapter {
  ingest(episode: Episode, namespace: Scope): Promise<MemoryWriteReceipt>;
  search(query: Query, namespace: Scope, budget: number): Promise<Candidate[]>;
  snapshot(namespace: Scope): Promise<string>;
  restore(snapshot: string, targetNamespace: Scope): Promise<void>;
}
```

`Services` supplies read-only exact archive access, existing telemetry bridge, model service, memory adapter, clock and budget ledger. Episode/Query/Candidate must have a JSON Schema: episode contains ordered event refs, commit/outcome/time; query contains text, stage, repo/version filters and allowed splits; candidate contains content, type, refs, score, validity range and provenance. All payload schemas are versioned; reject unknown major versions and invalid ranges. Byte references are half-open offsets into raw bytes. Protected text offsets refer to a declared UTF-8 decoded view and require a byte mapping; never mix token, character and byte offsets.

### Ordering, conflict and identity rules

1. Archive originals before any lossy transform. Preserve both stdout and stderr, exit/signal and tool-call association.
2. Protect explicit requirements, permissions, active code edits, exact error/test identifiers and pending tool pairs before selecting anything to omit.
3. Compress new observations before building summaries over the context view. Summary nodes must retain raw leaf refs; a summary is not the only surviving evidence.
4. Hierarchy may replace old spans; masking sees only remaining eligible observation segments. A source span has one owner per revision: reject overlapping replacements and double compression.
5. Retrieval candidates are filtered by namespace, split and validity before ranking, then deduplicated against active context. Stage changes ranking, never authorization.
6. Reversible encoding adds pointers for removed spans; final cache layout does not change provenance. Protected material and tool protocol validate last.
7. Extraction happens after an episode is closed and, in learning trials, after outcome validation. No mutation of frozen test memory. Memory writes and graph edges are transactional/versioned.
8. Disabled plugin is identity: no model calls, memory writes, prompts, tool-schema changes or timing work except a minimal flag check. Any unavoidable harness overhead is matched in the transport baseline.
9. Unsupported capability, DAG cycle, duplicate plugin ID, incompatible configuration or unsafe token budget fails configuration validation before launch. Alternative orderings require a named, predeclared arm and fixtures.

Build each delta transactionally. On failure preserve the previous valid view; if that view cannot fit, use a tested native compaction path or stop with `context_budget_exceeded`. Never drop arbitrary content to meet a cap. Timeout or schema failure selects deterministic/no-op fallback and emits one attributable event. Record intended treatment, applied treatment and fallback count; analyze by assigned arm as primary, applied-only results as sensitivity.

Optional sidecar: asynchronous summarization, embeddings, indexing and extraction use jobs keyed by `(namespace,input_hash,plugin_version,config_hash)`. Bound queue length, CPU, RAM and spend; return immutable artifacts. Apply only at a turn boundary if the input revision still matches. Stale jobs are discarded or retained as unconsumed artifacts, never committed into another run. Retries are idempotent, usage charged once per actual request, and all wasted work is included in overhead. Synchronous fallback must be deterministic; sidecar availability is pinned per arm.

## 5. Exact local archive and recovery API

Default: existing exact-content store if adequate; otherwise content-addressed files plus SQLite metadata/FTS5 under an experiment-owned directory outside agent worktrees. Store raw events and blobs separately from derived summaries/memories. SQLite is an index, not the sole copy of raw bytes. Blob key = SHA-256 of exact bytes; manifest includes size, MIME, source trace/tool IDs, sequence, repo commit and access namespace. Atomic temp-write + fsync + rename; finalize references only after durable write. Deduplicate by hash but authorize each reference independently. A shared hash never grants access to another namespace.

Retain originals through the study and the declared reproducibility window (default 90 days, configurable before runs). Encrypt sensitive local storage where available; restrict file permissions. Redacted exports are separate artifacts with mappings; never label a redacted representation an exact original. Credentials are excluded at collection boundaries; if existing logs already redact content, record the archive fidelity limitation. Immutable means application-level append-only and integrity checked, not a claim of tamper-proof storage. Authorized deletion creates tombstones and removes dependent retrieval availability without rewriting surviving historical manifests.

MCP or wrapper API contracts:

```text
archive.search(query, scope, cursor?, limit<=20)
  → [{ref, snippet, source_event_id, repo_commit, match_kind}], next_cursor
archive.get(ref, scope, byte_start?, byte_end?, max_bytes<=65536)
  → {bytes_or_text, sha256, total_bytes, returned_range, next_range, content_type}
archive.expand(summary_id, scope, depth=1, max_tokens=4000)
  → {children_or_originals, refs, omitted_count, next_cursor}
memory.search(query, scope, stage?, top_k<=5, max_tokens<=2000)
  → [{memory_id, type, text, evidence_refs, valid_for, score}]
```

Bind scope to authenticated run identity; do not trust caller-supplied owner/repo/split. Page large content, preserve exact Unicode/newlines/binary bytes, and expose hash verification. Short pointer example: `[tool observation archived: event=E42; sha256=…; failing tests retained; use archive.get]`. Charge pointer/schema tokens and every expansion. No compression policy may recursively compress recovery responses before the requesting agent can consume them; cap expansion size explicitly instead. Archive failure before output publication means return original, not an unrecoverable placeholder.

### Optional Supabase extension (not a milestone-zero dependency)

Keep `Archive` and `MemoryAdapter` interfaces unchanged. Use private Storage for exact blobs, Postgres for manifests/summary DAGs/episodes/principles/graph metadata and pgvector for derived embeddings. Use separate vector indexes/namespaces for incompatible embedding versions; store model and dimensions with each index. Supabase supports pgvector-backed vectors [S1]. Storage access must be scoped using authenticated policies [S2].

An authenticated Edge Function can validate requests, enforce scope and issue short-lived private-object access or enqueue work. Long summaries/local inference run in a bounded worker; do not assume Edge Functions support unbounded CPU or persistent local models. Apply owner/project/run authorization to every exposed metadata table and Storage path. Never ship a service-role secret to agents or clients. Local disk remains the write-ahead durable source until sync acknowledgement; offline retrieval uses local data. Verify remote checksums, retry idempotently, and test cross-tenant denial. Remote egress, storage, database, function and worker costs enter the treatment ledger. This is architecture only: no SQL/migrations or hosted resources are created by this handoff. Recheck current Supabase docs and limits before implementation.

## 6. Ten technique designs, hypotheses and fixtures

### 1. Observation masking (`mask`)

**Hypothesis:** Removing older low-value observations reduces repeated input cost with little quality loss. Mechanism: age/token-window selection of tool-result bodies, retaining short metadata and protected facts; keep user/assistant instructions and recent results intact.

Variants: off; retain last 5 versus 10 completed tool observations; token-based recent window (8k versus 16k). Tune on development replays only. Start with last 10. Preserve failing-test summaries and unresolved diagnostics until superseded by explicit evidence; do not infer resolution from age. Never leave dangling tool-call/result pairs. Full-history mutation capability is required.

API: `mask.propose(View, Event)`, config `recent_observations`, `recent_tokens`, `pin_unresolved`. Selection metadata records reason and exact omitted ranges. Fallback: unchanged view. Fixture: old log contains the only port/config constraint, a pending call, and a recent corrected result. Gate: all pinned spans survive; canary demonstrates old bodies actually leave submitted context. Measure omitted bytes/tokens, repeated rediscovery, critical omission and native-compaction interaction.

### 2. Deterministic/semantic tool-output compression (`tool_compress`)

**Hypothesis:** Structured filtering removes duplicate/noisy logs more cheaply than general summarization. Parsers for test output, compiler diagnostics, search results and repeated progress lines preserve failing test names, exact assertions/errors, paths/line numbers, exit status and representative stack frames. File reads containing source code default to exact excerpts with ranges, not rewritten syntax.

Variants: deterministic parser; semantic summarizer; deterministic then semantic for residual blocks above 8k tokens. Semantic strategy can use a fixed metered model or idea 9's local service; model/config are separately controlled. JSON output includes retained details and refs. No claims of semantic equivalence: validate identifiers and protected spans mechanically. Invalid parser format returns original. A semantic summary that grows beyond input is rejected unless a declared retrieval arm requires expansion.

API: `compress(toolName, originalRef, format, protectedSpans) → Segment`. Config `min_tokens=2000`, `max_output_tokens=1500`, format rules/version and semantic model hash. Fixture: repeated failures with two subtly different error codes, stderr warnings, Unicode, truncated streams and an exit-0 misleading message. Gate: exact status/critical identifiers retained, unsupported formats fail open, recovery hash matches. Track parser coverage, total agent calls, summary hallucinations and downstream omissions.

### 3. Hierarchical memory / LCM-style compaction (`hierarchy`)

**Hypothesis:** A summary DAG plus raw-leaf retrieval sustains long tasks more efficiently than a flat summary. Maintain L0 originals, L1 episode/span summaries, L2 summaries of L1 groups, each with source coverage and dependencies. Active context includes a bounded recent tail plus selected summaries. “Lossless” means originals remain recoverable; summaries themselves are lossy. LCM provides architectural inspiration [R3], not a claim of feature parity.

Variants: single-level summary; two-level DAG; extractive hierarchy. Initial trigger at 70% of usable context, target 50%; use actual installed model limits and reserve output/tool headroom. Summaries enumerate requirements, files changed, decisions with evidence, failed approaches, unresolved questions and next verification. Revalidate protected facts against leaves; do not rely solely on recursive prose. Max depth 3, fanout 8, pinned recent 8k tokens are development defaults.

API: `summarize(refs, level, budget)`, `expand(nodeId, depth, budget)`. Version summary nodes on changes; no in-place rewrite of raw history. Fixture: constraint appears only in L0; L2 carries its source coverage, expansion recovers it; repeated summarization does not erase an unresolved blocker. Gate: DAG acyclic, all coverage traceable, stale nodes excluded, summaries fit budget. Measure cumulative summarization cost, retrieval debt and detail retention over depth.

### 4. Reversible context compression (`reversible`)

**Hypothesis:** Replacing old verbose spans with exact-recovery handles enables smaller working context without irreversible information loss. This is distinct from merely keeping an archive invisible to the agent. Select spans by fixed age/size thresholds, create compact manifests and offer exact `get/expand`. Support exact structured extraction as an alternative to generated summaries.

Variants: handles only; extract + handles; summary + handles; matched lossy representation without model-visible recovery as an ablation (passive originals remain safe). Need verified history mutation for old-context replacement. Per-output handles can run on wrappers but are reported as narrower coverage.

Config `min_span_tokens=4000`, `manifest_tokens=256`, `expand_budget=4000`. Fixture: recovery of exact source code, JSON key order, long path, CRLF and binary blob; denied cross-run ref and missing blob. Gate: 100% byte equality for authorized round-trip fixtures, 100% access denial for forbidden fixtures, no orphan references. Track recovery latency, requested/recovered tokens, unsuccessful expansions, repeated expansions and avoided versus deferred tokens. Recoverability is not proof that the model will request the right evidence.

### 5. Self-hosted persistent Mem0 (`mem0`)

**Hypothesis:** Reusing repository facts and prior episodes lowers rediscovery cost on new tasks. Mem0 is an adapter implementing `MemoryAdapter`, never a hard dependency of the runner, archive or other plugins. Default disabled; baseline uses no learned memory. Pin self-hosted package/container/runtime, configured extractor, embedder, vector/history backend and storage paths; self-hosted does not imply local LLM inference. Explicitly meter any external calls. Official OSS documentation describes self-hosted/library deployment and configurable components [R4]; benchmark parity with managed services is not assumed.

Variants: no memory; raw-history FTS search; stock pinned self-hosted Mem0; version-aware append-only wrapper. Stock behavior and custom protections must be reported separately. If Mem0 mutates its internal records, preserve external immutable episodes and mutation receipts; snapshot all relevant backends consistently. Set inference mode/config explicitly, do not rely on defaults. Filter by repo, commit applicability, chronological cutoff and train/test split before search.

Fixture: a removed API convention conflicts with a newer version; retrieval rejects stale advice. Restart and restore produce equivalent candidate IDs/results on fixed queries. Gate: no test-write contamination, provenance round-trip, cost attribution and clean adapter disable. Measure ingestion/retrieval/maintenance costs, stale-memory rate and downstream transfer. If service unavailable, fall back to declared raw-history/no-memory mode and flag the assigned-arm failure.

### 6. Generalizable principle extraction (`principles`)

**Hypothesis:** Evidence-grounded principles transfer better than facts or raw episodes when tasks differ. ReasoningBank motivates learning from successes and failures [R1]; ACE motivates structured generation/reflection/curation [R2]. Implement a bounded post-episode extractor, verifier and incremental curator, not uncontrolled self-modifying instructions.

Principle schema: `id, version, title, mechanism, trigger, applicability, exclusions, procedure, counterexample, evidence_refs, source_repo_commits, outcome_evidence, confidence, valid_from, supersedes, status`. Distinguish independently verified outcome from model self-judgment. Example: “When a retry can repeat a write, verify idempotency at the persistence boundary”; include conditions, a concrete test method and evidence, not an entire patch recipe.

Variants: raw episodes; fact-only memory; principles-only; principles + exact supporting procedures. Compare success-only extraction against success+failure on training data. Use one fixed extraction prompt/model and cap of 5 candidates/episode; deduplicate by explicit curator delta (`add`, `supersede`, `reject`) without deleting originals. No claims of universal validity from one episode; quarantine contradictory/unsupported principles.

Fixture: failed attempt incorrectly self-reports success; a principle omits a crucial ordering step; conflicting dependencies require version scoping. Gate: every accepted claim has retrievable supporting evidence and applicability; no hidden grader contents enter memory. Measure verification rejection, procedural loss and incremental value over raw retrieval under equal context budgets. Extraction costs count even for rejected principles.

### 7. Stage-aware retrieval (`stage`)

**Hypothesis:** Different work stages benefit from different memory types. Investigate favors symptoms/files/previous failures; plan favors constraints and architectural principles; implement favors exact APIs and procedures; test favors regressions and diagnostic history; review favors invariants and acceptance evidence.

Use a deterministic signal from recent tool/activity types as initial classifier, with `unknown` when confidence <0.7; optional local classifier is a separate idea-9 arm. Stage changes can be reversible and confidence logged. Do not pretend that a compiler call always means testing; inspect context signals.

API: `inferStage(events) → StageSignal`; `rank(query,candidates,stage,tokenBudget)`. Initial retrieval top-k 5, budget 2k tokens, invoked at start and stage transitions; no automatic per-turn memory flooding. Variants: stage-agnostic same retrieval backend/budget; stage-aware; fixed oracle stage labels for a small diagnostic subset. Fixture: rapid investigate↔test transition and unknown stage. Gate: no permission changes, deterministic stage output on fixed fixtures, retrieval caps respected. Measure retrieval precision/recall on labeled evidence, stage error and success conditional on stage confidence.

### 8. Knowledge graph (`graph`)

**Hypothesis:** Relational links identify useful evidence missed by independent vector/keyword records. Nodes: versioned code symbol/file, episode, diagnostic, test, principle. Edges: `depends_on`, `observed_in`, `fixed_by`, `supports`, `contradicts`, `valid_for`. Every edge includes source refs, extraction method/confidence and commit/time validity. Start with a local adjacency index; no graph service is required.

API: `neighbors(nodeId, edgeTypes, maxHops<=2, scope)` returning scored candidates and paths. Reuse fixed parsers for code links; uncertain LLM edges remain candidates. Retrieval combines FTS/vector seeds plus bounded graph expansion, with the same final token budget as non-graph comparator. Config `max_hops=2`, `max_candidates=50`, `max_tokens=2000`.

Variants: same memories flat; graph expansion; graph with/without inferred edges. Fixture: renamed symbol, two same-named files, obsolete dependency and contradictory principles. Gate: no timeless conflation of symbols across commits, source-backed edges, bounded traversal and cycle handling. Measure graph build/update cost, useful expansion rate, stale edge errors and extra hops. Compare against matched flat retrieval, not against a weaker no-memory baseline alone.

### 9. Local lightweight models (`local_model`)

**Hypothesis:** A small local selector/reranker/summarizer can replace expensive semantic processing with a favorable quality/energy/latency trade-off. Provide `score(query,chunks)`, `summarize(refs,budget)` and optional `classifyStage(events)` behind a strategy service used by ideas 2/3/7. A test of idea 9 must name which service it replaces; it is not meaningful as an unused standalone switch.

Variants: deterministic selector; pinned small encoder/reranker; pinned quantized instruction model. Record weights/tokenizer hashes, license, quantization, runtime, threads, accelerator, sampling settings, CPU/RAM and warm-up. Do not assert a particular model fits the user's hardware before audit. No fine-tuning. Training/test traces cannot enter an unapproved remote fallback.

Set per-call timeout and memory cap from development benchmarks; initial p95 latency budget 2 seconds for ranking, 10 seconds for summaries. On timeout or low confidence use deterministic ranking/exact excerpts, charging wasted compute. Fixture: distinctive one-line constraint amid repeated logs; untrusted embedded instructions; non-English/Unicode identifiers; long input and memory pressure. Gate: critical-span retention, no model-executed tool commands, bounded resources. Report CPU-seconds, peak RAM, Joules/kWh when measurable, cold/warm latency and end-to-end net cost. Keep power estimates labeled and avoid counting the whole machine's idle draw twice.

### 10. Cache-aware compaction (`cache`)

**Hypothesis:** Fixed stable prefixes and less frequent, strategically timed context changes can reduce paid processing even when raw token count is higher. API prompt caching depends on model-specific rules and actual observed usage [O4]. Do not hardcode historical discounts, thresholds, retention or cache-write rules.

Keep instruction/tool schema ordering and stable repository metadata deterministic; append changing context later. Avoid timestamps/run IDs in shared prefixes unless needed for correctness. Version changing memories as an explicit suffix/block. Prefix hashes and longest-common-prefix token lengths are diagnostic proxies, not proof of provider cache hits. Default policy: compact only at 70% context pressure or when projected multi-turn saving exceeds rewrite/summary cost plus estimated lost cache benefit; use a fixed documented planning horizon of 5 turns, with coefficients frozen after development. Compare to pressure-only compaction at the same limits. No online policy training.

API: `layout(view,stablePrefixVersion)`, `shouldCompact(usageHistory,pressure,rateCard)`. Variants: native layout; stable layout; stable layout + delayed compaction. Audit whether provider cache controls are actually exposed by the chosen Codex route before setting any. If unavailable, test layout/timing alone.

Fixture: timestamp/tool-order changes invalidate a prefix; shorter context increases uncached charges; cache-write categories differ by model; missing cache counts. Gate: accurate usage normalization, safe headroom, no invented cache savings, same semantic/protected content. Measure realized cached/ordinary/write tokens, rate-weighted cost, cache-busting frequency and compaction break-even. Preserve native ordering when protocol requires it.

## 7. Configuration and pipeline example

Ship a schema-validated YAML format. Unknown keys/plugins are errors. Resolve defaults once into `resolved-config.json`, include source hashes and freeze it before scheduling. Config changes create a new variant ID. Paths below are placeholders; commands must reject unresolved required fields.

```yaml
schema_version: 1
experiment:
  id: codex-context-pilot-v1
  protocol: EXPERIMENT_DESCRIPTION.md
  seed: 41017                 # scheduler seed, not a claimed model seed
  mode: shadow
  pricing_snapshot: REQUIRED
  max_total_usd: REQUIRED
runner:
  adapter: codex_cli
  binary_version: REQUIRED
  model: REQUIRED
  auth_route: REQUIRED        # metered_api | subscription
  profile: REQUIRED
  concurrency: 1
  isolated_home: true
  matched_native_compaction: true
observability:
  mode: reuse_existing
  adapter: REQUIRED
  source_of_truth: REQUIRED
  add_missing_tags_only: true
archive:
  backend: local_content_addressed
  root: ./state/archive
  index: sqlite_fts5
  verify_on_read: true
  retention_days: 90
memory:
  adapter: none               # none | raw_fts | self_hosted_mem0
  snapshot: empty-v1
  writes: false
  namespace_template: '{experiment}/{split}/{variant}/{run}'
plugins:
  mask: {enabled: false, recent_observations: 10, recent_tokens: 8000, pin_unresolved: true}
  tool_compress: {enabled: false, strategy: deterministic, min_tokens: 2000, max_output_tokens: 1500}
  hierarchy: {enabled: false, strategy: extractive, trigger_fraction: 0.70, target_fraction: 0.50, max_depth: 3, fanout: 8}
  reversible: {enabled: false, min_span_tokens: 4000, manifest_tokens: 256, expand_budget: 4000}
  mem0: {enabled: false, endpoint: null, version: null}
  principles: {enabled: false, max_per_episode: 5, evidence_required: true}
  stage: {enabled: false, strategy: deterministic, confidence_floor: 0.70, max_tokens: 2000}
  graph: {enabled: false, max_hops: 2, max_candidates: 50, max_tokens: 2000}
  local_model: {enabled: false, roles: [], model_manifest: null}
  cache: {enabled: false, strategy: stable_prefix, planning_horizon_turns: 5}
pipeline:
  phases:
    capture: [archive_original]
    observation: [protect, tool_compress]
    retrieval: [stage, mem0, principles, graph, retrieval_budget]
    context: [hierarchy, mask, reversible, cache, validate]
    post_episode: [principle_extraction, memory_snapshot]
  disabled_nodes: identity
  on_error: previous_valid_view
sidecar: {enabled: false, max_queue: 16, max_workers: 1}
budgets:
  task_wall_seconds: 1800
  max_tool_calls: 150
  max_request_attempts: 100
  max_agent_output_tokens: 20000
  task_usd: REQUIRED
  overhead_usd: REQUIRED
acceptance:
  executor: isolated_trusted_grader
  timeout_seconds: 600
  reject_test_tampering: true
```

Plugin-local service roles are declared in the schema: enabling local summary requires tool_compress or hierarchy with `strategy: local`; enabling local rank requires an active retrieval selector. Enabling principles at retrieval and extraction phases uses one plugin identity and distinct phase operations. A memory adapter can supply facts without principles; graph can index raw episodes without Mem0; stage can rank raw FTS results; hierarchy can summarize without Mem0, graph or local models. Validator must demonstrate all these independent combinations.

## 8. Task suite and isolation

Select about ten *real* unresolved or historically reconstructed development prompts from the owner's repos. The package supplies a manifest template, not fabricated claims about access to specific repos. Discover candidate issues/commits with the owner; freeze the final suite before running. Aim for 2–4 repositories and a range of natural task sizes. Exclude tasks whose grading requires inaccessible services or unstable external state unless a fixture exists.

| Slot | Representative task to select | Acceptance evidence |
|---|---|---|
| T01 | Reproduce and fix a focused logic regression | New independent regression plus existing unit suite |
| T02 | Fix a noisy multi-test/compiler failure | All intended failures resolved; unrelated suite green |
| T03 | Small multi-file feature with API contract | Contract/integration tests and compatibility checks |
| T04 | Refactor duplicated behavior without interface change | Behavioral equivalence/invariant tests |
| T05 | Dependency/API migration at pinned versions | Build plus old/new behavior fixtures |
| T06 | Retry/concurrency/idempotency defect | Deterministic race/retry fixture |
| T07 | Config or deployment-script defect | Isolated config validation; no production deployment |
| T08 | Frontend/state/accessibility regression | Deterministic browser/component acceptance |
| T09 | Repository-specific convention learned in an earlier episode | Held-out downstream tests; chronology recorded |
| T10 | Transfer of a principle to a different module/repo | New scenario tests without copied solution |

T09–T10 form a separately reported memory-dependent subset if certified; do not force memory dependence on ordinary issues. For that subset, run development diagnostic conditions with no relevant history versus curated sufficient evidence (oracle). Failure under both means the task may exceed agent ability; success under both means it is not certified memory-dependent. Oracle selection is performed before holdout evaluation, never from test-run failures. Report certification selection bias.

Each task manifest must include prompt exact bytes/hash, repo path and commit, dependency lock hashes, OS/container requirements, environment/service fixtures, installation and public-test argv, private grader reference/hash, expected behavioral requirements, forbidden changes, budget and optional history cutoff. Independent tests are authored or reviewed without using treatment outputs, must fail on the defective base and pass on a verified reference solution when available. A reference solution is never mounted in agent worktrees. Do not invent tasks or expected patches from the current answer.

Launch a clean Git worktree or isolated checkout at the exact base commit for every run; use detached execution, no shared writable build directories, distinct ports/databases and isolated temp paths. Worktrees share Git object storage, so if history reveals answers or repo hooks are dangerous use a history-restricted disposable checkout/container. Freeze instruction/skill/MCP assets and their hashes. Agent-generated tests can aid coding but never replace the trusted grader. Evaluate final patch in a clean trusted environment; protect grader scripts and expected outputs from agent writes. Human review, if needed, is blind to treatment and rubric-scored.

Persist patch, untracked-file manifest, exit status, termination cause and final clean-grader report. Ignore the agent's claim of success. Passing acceptance requires all mandatory behavioral tests, build/type checks required by task and no forbidden changes. A passing implementation can differ from the reference patch.

### Leakage controls

Within-session study: independent empty memory namespaces for each task/variant/replicate; no cross-run retrieval, shared result files or learned indexes. Freeze initial caches/dependencies or declare them shared read-only. Disable uncontrolled native persistent memory where supported; otherwise document it and separate contaminated cells.

Cross-session study: chronological train/development/test episodes, no duplicate issues/patches across splits, no future commit data, no target answer in history. Build frozen memory checkpoints from training episodes only (0, 5, 20 episodes if available); restore an identical checkpoint into every compared test run. Evaluate read-only. Training ingestion/curation costs are included and amortized explicitly. A separate exploratory online chronological track can update between tasks, but has independent memory per arm and no writes from future tasks. Never pool its results with frozen holdout results.

Use cross-repository holdout for generalization when enough repos exist. Include unrelated-memory negative controls and provenance checks. Do not expose private acceptance-test text, reference solutions, outcome commentary or later task prompts to extraction. Verified pass/fail labels may label completed training episodes without importing grader internals.

## 9. Variants, ablations and execution allocation

Avoid 2^10 exhaustive testing. Every technique must be represented in component/shadow evaluation; live eligibility depends on audit and gates. Preserve the priority order for implementation and reporting.

| Arm | Configuration | Primary comparator |
|---|---|---|
| B0 | Native Codex, no experiment prompt/tools/intervention | Practical native reference |
| B1 | Same adapter/tools/schema as treatment, transformations identity | Main transport-matched control |
| I1 | B1 + masking | B1 |
| I2d / I2s | Deterministic / semantic output compression | B1; I2d vs I2s |
| I3 | Hierarchy, with minimum archive capability only | B1 |
| I4 | Reversible handles/excerpts + recovery | Schema-matched B1 |
| Mraw | Frozen raw-history FTS retrieval | Equal-budget no-memory control |
| I5 | Stock self-hosted Mem0 facts | Mraw and no-memory control |
| I6 | Principles with exact evidence using raw adapter | Mraw; fact-only memory |
| I7 | Stage-aware ranking of fixed Mraw candidates | Stage-agnostic Mraw |
| I8 | Graph expansion of same frozen memories | Matched flat retrieval |
| I9 | Local strategy substituted for a named I2s/I7 service | Same pipeline with deterministic or paid strategy |
| I10 | Stable-prefix layout + declared compaction policy | Same underlying pipeline, cache policy off |
| C12 | I1 + I2d | B1, I1, I2d (2×2 interaction) |
| C34 | I3 + I4 | B1, I3, I4 |
| Cbase | I1 + I2d + I4 | Best eligible single; remove each component |
| Ccache | Cbase + I10 | Cbase |
| Cmem | I5 + I6 + I7 (same frozen corpus) | I5; minus-principles; minus-stage |
| Cgraph | Cmem + I8 | Cmem |
| Clocal | Selected Cbase/Cmem + named I9 replacement | Exact same configuration without replacement |

Necessary infrastructure does not invalidate independent toggles. For example I3 can use exact archived refs without enabling I4's handle substitution; I6 can store/retrieve principle records without Mem0; I8 can link episodes without principles. If prerequisites are unavailable, mark ineligible with cause instead of enabling hidden treatments. Schema-matched controls can advertise tools that return no relevant records, but record their prompt-token cost and distinguish them from B0.

Allocation, frozen before spend:

1. Offline fixtures/replays: all arms on development traces, 0 live coding runs.
2. Shadow: B0/B1 live sessions on 2 non-holdout development tasks; proposed changes not submitted. Meter sidecar work. Compare passive observation overhead.
3. Small pilot: 3 development tasks × 2 replicates × at most 6 nominated arms = at most 36 coding runs. Nominate by priority, eligibility and offline gates, initially B0/B1, I1, I2d, I4, Cbase where supported. Later memory pilots use their own comparable arms within a declared budget increment.
4. Main ten-task pilot: 10 frozen real tasks × 3 replicates × baseline + up to 3 preselected optimized arms = 120 coding runs maximum. If B0 and B1 differ materially, retain both and reduce optimized arms or revise budget before launch. Selection happens using development data only. Unsupported single ideas remain documented offline/shadow outcomes; advancing them later requires a new allocation.
5. Cross-session evaluation: separate frozen-history task subset/track and budget; compare no memory, Mraw, I5 and one selected principle/stage combination. Report ordinary and memory-dependent tasks separately.

The default does not promise 120 runs are affordable. `plan` prints worst-case agent + overhead cost and refuses to start above the explicit owner-supplied cap. Budget cuts reduce arms/repeats using a predeclared rule, never omit expensive failed runs after seeing results. A larger 50–100-task confirmatory study is optional only after owner authorization, not part of the default ten-prompt scope.

For valid 2×2 interactions calculate `(C12 − I1) − (I2d − B1)` on per-task costs and separately on success. Leave-one-out combined arms identify interactions but do not establish universal component effects. Do not rank all ten by unrelated or underpowered live samples.

## 10. Execution protocol and proposed CLI contract

Implement `ctxexp` with machine-readable outputs and a dry-run default. It is a proposed harness executable, not present in this package. All subprocesses use argv arrays, no interpolated shell commands; inherit an allowlisted environment, apply timeout and terminate/reap the process tree. Preserve redacted launch metadata, not credentials. Never auto-run repository scripts during discovery without the appropriate repo trust/permissions.

```bash
ctxexp audit --config configs/experiment.yaml --out audit/
ctxexp tasks validate --manifest tasks/tasks.yaml --check-base-fails
ctxexp config validate --config configs/experiment.yaml --capabilities audit/capabilities.json
ctxexp plan --config configs/experiment.yaml --tasks tasks/tasks.yaml --out plans/main.json
ctxexp replay --plan plans/replay.json --traces existing-export.jsonl --split dev
ctxexp shadow --plan plans/shadow.json
ctxexp run --plan plans/pilot.json --execute
ctxexp run --plan plans/main.json --execute
ctxexp session launch --plan plans/main.json --run-id T03-Cbase-r2 --execute
ctxexp accept --run-id T03-Cbase-r2 --trusted-grader graders/registry.json
ctxexp report --plan plans/main.json --include-failures --out reports/main/
ctxexp reproduce --run-manifest runs/T03-Cbase-r2/manifest.json --dry-run
```

Commands return exit codes: 0 completed command (inspect result success separately), 2 invalid config/task, 3 unsupported capability, 4 run infrastructure error, 5 budget stop, 6 archive/integrity failure. Each launched run has immutable manifest, config, prompt, pair/replicate IDs, exact command argv, dependency hashes, memory snapshot, usage joins, patch and outcome. `reproduce` checks availability and version drift; it cannot guarantee identical nondeterministic model outputs.

Underlying supported CLI example after auditing installed help and trusted profile (profile defines agreed permissions):

```bash
codex exec --json --profile EXPERIMENT_PROFILE --model PINNED_MODEL - < prompt.txt
```

Run with process working directory set to the isolated worktree. Capture stdout JSONL and stderr separately with the existing instrumentation. Do not assume this output alone contains complete tool originals or exact invoices. If installed flag syntax differs, generated argv must follow the pinned binary's help and recorded audit. No subscription-to-API credential conversion is assumed. API credentials belong in a protected model-call boundary; do not expose them to arbitrary repository scripts.

Within each `(task, replicate, route, model, commit)` block, randomize treatment order using the scheduler seed. Same task prompt bytes, base commit, tool schemas for matched control, permissions, model/reasoning settings, dependency environment, hardware allocation, budgets and acceptance rubric. Record model sampling/seed only when supported; otherwise use independent fresh sessions and report that provider nondeterminism cannot be seeded. Do not pass invented seed flags.

Primary scheduling concurrency is 1 to limit CPU/cache/resource contention; if later parallelized, block by hardware and record load. API model aliases may drift: store resolved identifiers when returned, date/time and provider fingerprint if available; pause/reblock if versions change. Keep cold/warm model-runtime state and provider cache timing balanced. Provider caches may be impossible to flush; label observed cache state and time gap, rather than claim isolation. Do not inject arbitrary prompt nonces into the primary cache study to force misses: they change the intervention. Separate cold/warm sensitivity runs use a documented supported mechanism or are explicitly uncontrolled.

Retries inside the agent/transport count toward the same run and its budgets; no free replacement of unsuccessful attempts. An infrastructure-invalid pair may be rerun only under a predeclared reason code with original spend retained in the campaign ledger. Hard wall-clock/tool/request caps include recovery and memory calls. Provider calls in flight can overrun monetary caps by a bounded amount; reserve one maximum-request allowance and report actual overrun.

## 11. Metrics, normalization and accounting

Existing observability is authoritative. Build queries/adapters into its data; keep joins and rate calculations reproducible. Report unknown usage coverage. Do not infer hidden reasoning content or reconstruct unavailable token detail.

| Outcome | Operational definition |
|---|---|
| Success | Independent mandatory acceptance tests pass; no forbidden modifications |
| Paid API cost | Attributable metered charge where available/reconciled; currency and evidence recorded |
| API-equivalent cost | Observed compatible usage × dated API rate card; explicitly estimated for subscription sessions |
| Cost per successful task (CPST) | Sum of costs for **all** scheduled valid attempts, including failed/timed-out ones, divided by successful attempts |
| Token usage | Provider input total, cached input, ordinary input, cache-write categories if applicable, output and reasoning-output inclusion semantics |
| Latency | End-to-end agent time, grading time, model/tool/retrieval/sidecar time; p50/p95 and critical path, not summed overlapping spans |
| Local resources | CPU-seconds, peak resident memory, accelerator use, energy measurement/estimate and electricity tariff |
| Tool activity | Counts by type, retries, expansions, redundant calls; intercepted/total eligible traffic |
| Compression | Original eligible tokens / transformed tokens at event and submitted-request level; include pointers/tool-schema overhead |
| Expansion | Expanded tokens / omitted tokens, expansion calls, unfulfilled requests; repeated expansions counted |
| False omission | Required annotated facts omitted or distorted / required annotated facts in eligible source; critical subset separate |
| Recovery | Exact round-trip fidelity, authorized retrieval success, retrieval latency and stale/missing refs |
| Cache effects | Observed cached/total input, cache-write counts, prefix-change rate and actual cost changes after compaction |
| Transfer | Held-out cost/success deltas vs no memory and Mraw; repeated-failure avoidance, stale advice, evidence utility |

Do not report “cached output tokens” unless the actual provider defines and meters them. For ordinary API reporting, cached-vs-uncached applies to input; output is separately priced. Do not double count reasoning output if included in provider output total. Preserve raw provider fields alongside normalized fields.

For each model/rate regime, define disjoint token charge buckets `b` and prices `p_b`; modeled cost = `Σ_b tokens_b × p_b / 1e6 + attributable non-token fees`. Some models expose separate cache writes, others do not. Never assume `input - cached` is the full ordinary bucket without checking schema. If write counts are absent but required for exact modeling, report an interval/unknown, not zero. Cache rules and prices are locked at the experiment date [O4]. Validate normalization against fixtures for every supported provider schema. Cost credited/refunded by provider is a separate adjustment with evidence.

`run_operating_cost = agent inference + summary/extraction/embedding/reranker inference + retrieval/service charges + local incremental electricity + attributable storage/egress`. Include failed/rejected summaries, sidecar work discarded as stale, memory construction and attempts that never reach acceptance. Deduplicate shared spans by authoritative request IDs, never count both turn-cumulative totals and individual requests. Missing usage remains missing and blocks exact-cost claims.

For frozen cross-session memory report both (a) full ingestion charged to the observed evaluation cohort and (b) amortized cost at predeclared 10/100/1000 downstream uses. Avoid treating historically spent construction as free. Training runs, curation and manual review remain in campaign totals.

Report three economic views: operating CPST; campaign cost including all setup/pilot/failure spend; engineering-inclusive CPST with recorded engineering hours × a declared hourly rate divided across a specified adoption horizon. Show break-even task count = fixed engineering cost / expected per-task operating saving when saving >0. Engineering estimates are not invoice charges. Keep cash, API-equivalent and fully loaded views separate; never add metered and estimated prices for the same call.

For subscriptions, report observed usage, capacity/limit signals if available, and estimated API-equivalent costs. Report incremental paid usage only when billing evidence supports it. A fixed subscription allocation is an optional accounting scenario, not proof of invoice savings. Less token use does not imply a lower subscription bill. Do not extrapolate API cache pricing to undocumented subscription invoicing.

Energy: measure incremental energy against matched idle/load when possible; use kWh × declared tariff. If no suitable meter exists, report CPU and power-model range with uncertainty; do not present inferred Joules as exact. Include warm-up once per declared deployment horizon and show sensitivity.

False omissions require a pre-labeled development fixture corpus, independent annotation/blind review, or evidence-backed postmortems. Missing agent retrieval does not prove an omitted fact was irrelevant. Track harmless omission, critical omission, distortion and unsupported added claim separately. Trace repeated rediscovery and archive expansion to source IDs; do not rely solely on an LLM judge.

## 12. Analysis plan and predeclared gates

Freeze `analysis-plan.md` before holdout runs. Unit of generalization is task (or repository when enough repos), not individual turns. Repeats estimate stochastic variability within task and are not independent tasks.

Primary estimator: pooled CPST ratio treatment/baseline on the same eligible task/replicate blocks and route. Include all treatment-assigned valid attempts regardless of fallback. Zero successes means CPST infinite/undefined and explicitly a failed candidate. Also report each task's mean cost, success fraction, paired cost difference/ratio and latency; a successful-only cost table is secondary and selection-biased.

Use task-cluster paired bootstrap (10,000 resamples; all paired arms/repeats retained within a task) for 95% intervals on CPST ratio, success difference and mean cost. With ten tasks intervals are unstable; show raw task data, leave-one-task-out sensitivity, median effects, standard deviation/IQR and baseline variance. Use paired permutation tests for exploratory cost differences and paired binary discordance summaries/McNemar only when pairing/sample assumptions hold; do not treat repeated trials as independent discordant tasks. Stratify ordinary versus memory-dependent tasks and route; do not pool API invoices with subscription estimates.

Preselect one primary optimized-vs-baseline confirmatory comparison after development. Other arms are exploratory; if multiple confirmatory contrasts are retained, use Holm correction and report unadjusted effect sizes plus adjusted inference. Do not claim noninferiority from a non-significant difference. Proposed larger-study success noninferiority margin is −5 percentage points: lower confidence bound on treatment-minus-baseline success must exceed −0.05. Ten tasks are generally insufficient; label the result inconclusive if interval is wider. CPST target: point estimate ratio ≤0.80, with upper 95% bound <1 for a confirmatory savings claim. A 0.70–0.80 ratio is the earlier target range, not a required pilot finding.

Estimate confirmatory task/repeat needs by simulating/resampling development task-level cost/success variability for 20% savings and the success margin, then state achievable power under the cap. If unaffordable, deliver an honest pilot, not an underpowered definitive claim. Do not enlarge sample opportunistically to rescue significance.

Default gates (freeze or explicitly revise before outcomes):

- **G0 integration:** all exact-recovery/protocol/namespace fixtures pass; required metric joins complete; baseline identity passes. Any archive corruption, unauthorized retrieval, changed permissions or hidden grader exposure immediately stops the affected pipeline and quarantines its data.
- **G1 offline:** zero critical-detail omissions in the protected fixture set; exact recovery 100%; median eligible-output reduction ≥20% for a compression candidate; projection includes overhead and at least nonnegative net saving. Retrieval-only candidates instead require labeled evidence recall ≥90% within the declared budget. These are screening thresholds, not proof of live safety.
- **G2 shadow:** zero invalid tool pairs, unintended submitted changes or unexplained baseline differences. Sidecar/model overhead remains within declared per-run overhead cap. Record actual interception coverage.
- **G3 small pilot:** candidate must have observed success at least baseline on the same pilot tasks, no critical omission and median added preprocessing latency ≤10% of baseline end-to-end runtime (or explicitly approved latency trade-off). Advance at most three; tie-break by lower all-attempt CPST then simpler pipeline. No significance claims here.
- **G4 resource stop:** stop scheduling at 90% of campaign cap, reserve remainder for in-flight calls and grading. Stop a candidate after two consecutive adapter/protocol failures or overhead >25% of baseline mean run cost in two pilot runs. Keep spent costs and failure reasons.
- **G5 live safety:** a critical omission causing incorrect patch or unsafe action stops affected configuration pending diagnosis/versioned fix. A fix creates a new arm; do not blend pre/post-fix results. Human interruptions and environment failures get explicit outcomes.
- **G6 promotion:** all safety gates, confirmatory criteria above, no unexplained telemetry gaps, practical latency/resource acceptance, and reproducibility artifact completeness. Otherwise retain as experimental/inconclusive.

Failure taxonomy: agent incorrect, acceptance regression, task timeout, request/tool budget, monetary cap, user interruption, environment setup, flaky grader, provider outage/rate limit, adapter/protocol error, archive corruption, memory leakage/staleness, semantic omission/hallucination, local-model timeout/OOM, telemetry missing. Log first cause, contributing causes, last valid view, source refs and total cost. Never silently relabel treatment-induced failures as infrastructure exclusions. Record inclusion/exclusion decisions blind to relative cost wherever feasible.

## 13. Stages, fixtures and benchmarks

Offline replay transforms recorded observations/contexts and measures fidelity and expected usage; it does not establish an agent's counterfactual behavior, success or realized cache hits. Shadow proposes changes while the live agent receives normal context; it measures compatibility and overhead, not savings. A branching continuation test is stronger: fork from an identical repository snapshot and permitted visible history at a checkpoint, resume with full versus transformed views using a verified interface, and grade continuations. If no faithful resume interface exists, mark unavailable rather than simulate hidden state.

Required fixture suite:

1. Identity pipelines: original bytes/protocol unchanged, no hidden model work, same configured tools.
2. Archive: crash during write, duplicate blobs, exact Unicode/CRLF/binary recovery, missing ref, digest mismatch, range boundaries and forbidden namespace.
3. Protocol: streamed/split tool outputs, tool errors, cancellations, retried model requests, pending call pairs, opaque items, native compaction and stateful continuation.
4. Fidelity: old one-line requirement, duplicate-but-different errors, path/line identifiers, corrected facts, source syntax and unresolved diagnostics.
5. Memory: empty snapshot, frozen restore, contradictory/stale advice, poisoned instructions, cross-repo entity collisions, forbidden future/test records.
6. DAG/config: independent disable, supported reorder, cycle/conflict, double span ownership, strategy prerequisite and unused local-model flag rejection.
7. Accounting: cached/write/output bucket variants, cumulative usage deduplication, missing costs, failure-only arm, zero-success CPST, discarded sidecar spend.
8. Evaluation: known-bad base fails grader, reference succeeds, grader/tamper attempt rejected, deterministic external-service fixture, flake handling.
9. Resource: local OOM/timeout, sidecar backpressure/stale revision, disk full and service outage; deterministic fallback or explicit safe stop.
10. Cache: stable versus changed prefixes, schema reordering and compaction with lower tokens but higher modeled cost.

Benchmark tiers: (a) these deterministic contracts; (b) captured real development trace corpus; (c) ten private real prompts with independent grading; (d) optional public SWE-bench Verified or Terminal-Bench subset for external validity under official pinned graders. Public benchmark work is optional and must not replace the owner's tasks or spend beyond the approved allocation. Public historical model contamination and different harnesses limit comparisons. Reuse a small long-context retrieval stress fixture for hierarchy but do not equate retrieval scores with coding performance.

## 14. Deliverables, milestones and definition of done

| Milestone | Concrete output | Done / exit criterion |
|---|---|---|
| M0 discover | Audit, source map, capability/cost reconciliation | Existing observability reused; no unsupported treatment claimed |
| M1 contracts/isolation | Schemas, validator, runner plan, exact archive adapter | Identity, isolation, recovery and budget fixtures pass |
| M2 ideas 1–4 | Independent transforms/recovery tools | Offline/shadow gates; exact provenance and fallback |
| M3 pilot | Frozen tasks, independent graders, randomized plan | Paired pilot report includes all failures/overhead |
| M4 ideas 5–8 | Mem0 adapter, principle schema/curator, stage ranker, graph | Frozen snapshots, leakage/stale-memory tests; raw baseline |
| M5 ideas 9–10 | Local strategy service and cache policy | Resource bounds, cache accounting and matched comparators |
| M6 main evaluation | Predeclared selected live runs and transfer track | Allocation/cap respected; valid acceptance and trace joins |
| M7 report/reproduce | Research report, data dictionary, redacted archive manifest | Every claim traceable to tasks/config/results; limitations explicit |

Do not schedule durations until the audit identifies actual integration effort. Implement in listed priority order, with cache accounting validated early as measurement infrastructure even though idea 10's policy is last. Stop after each milestone's deliverable if the next stage lacks prerequisites or paid-run budget; report the concrete blocker rather than rebuild observability.

Final implementation deliverables: versioned package/lockfiles, schemas and examples, capability registry, existing-telemetry adapter, local archive/recovery, ten independent plugins, optional sidecar, reproducible launcher, tasks and protected graders, fixtures, run manifests, all-attempt results CSV/Parquet, paired analysis, costs/rate-card snapshots, failure catalogue, docs and a minimal operator runbook. Optional Supabase deployment remains a separate extension deliverable.

Definition of done for the *implementation*: all ten designs have implemented and tested toggles or an explicit verified integration blocker; no hidden dependency on Mem0/Supabase; no invented billing claims; exact originals recoverable; no leakage; baseline plus eligible selected arms executed under frozen plans within budget; independent acceptance results; analysis includes failures, overhead and uncertainty; user can launch/reproduce a session from a manifest. An unsupported technique is not “implemented” simply because it has a config switch. Record partial completion honestly.

Definition of done for this *specification package*: standalone design, numbered scope, contracts, templates, audit/checklist, execution/analysis protocol and agent handoff delivered. No full system, repository changes, live sessions or hosted resources are implemented by preparing this package.

## 15. Research/paper reporting outline

1. Motivation and questions: context cost versus usable experience; scope limited to Codex and these ten mechanisms.
2. Related work: masking/compression, LCM-style archive hierarchy, Mem0, ReasoningBank, ACE; distinguish vendor/author benchmarks from independent evidence.
3. System: plugin DAG, immutable archive, adapter capability boundaries, existing observability integration.
4. Experimental protocol: tasks/splits, graders, models/auth routes, budgets, repeats, randomization, cache controls and leakage prevention.
5. Results: per-task paired success/cost; pooled all-attempt CPST; intervals and heterogeneity; native versus transport baseline.
6. Ablations/interactions: masking×compression, recovery, principles versus raw history, stage, graph, local replacement and cache policy.
7. Mechanisms: omission/recovery, cache busting, procedural loss, transfer and overhead.
8. Economics: exact versus modeled charges, subscription limits of inference, local energy, engineering amortization/break-even.
9. Failure cases and validity threats: ten-task sample, stochastic APIs, task/model drift, noisy energy, selection effects and unsupported surfaces.
10. Reproducibility/data governance: code/config/task hashes, redacted exports and private-repo limitations. State inaccessible artifacts and reproduction instructions.

No result tables should contain invented findings. Publish null/negative results and ineligible arms. Suggested result columns: task, variant, replicate, assigned/applied treatment, route, model/version, success, failure code, paid/modeled cost, cached/ordinary/write/output tokens, agent/overhead cost, runtime, omissions, expansions, snapshot, manifest and trace join IDs.

## 16. Reusable coding-agent prompts

### Initial handoff

Read EXPERIMENT_DESCRIPTION.md and CHECKLIST.md. This is a specification to implement incrementally, not authorization for paid experiments. Start M0 by inspecting repository instructions, existing observability and installed Codex capabilities. Reuse existing tracing/token/cost logs and hooks; do not build observability. Produce the audit, gap-only changes and one harmless joined compatibility example. Distinguish supported interfaces from experiments, and report missing source documents without inventing them. Do not change global user configuration. End with concrete audit artifacts and next milestone prerequisites.

### Component implementation

Implement only milestone [ID] from the frozen specification. Use the common contracts and independent flags. Preserve immutable originals, provenance, namespace boundaries and transactional fallback. Write the required behavioral fixtures, including disabled identity and failure cases. Use the audited adapter rather than presumed hooks. Report changes, verification, exact integration coverage and outstanding limitations. Do not start paid runs or optional hosting.

### Evaluation execution

Given an authorized budget and frozen plan [PATH], validate all hashes/capabilities, memory snapshots, isolation and independent graders. Execute only scheduled cells; preserve every attempt and its costs. Stop under predeclared gates. Do not tune from holdout results or discard failed attempts. Produce a paired report using existing observability as source of truth; label exact paid versus modeled/subscription costs.

### Failure analysis

Analyze run [ID] from its manifest, trace and exact archive. Separate environment, adapter, context omission, memory and agent causes. Cite source event/ref IDs; recover originals to verify suspected omissions. Retain the attempt/cost. Propose a fixture and a versioned fix; do not merge pre/post-fix outcomes into one arm or alter the holdout grading rubric.

## 17. Evidence and source registry

Sources accessed 4 November 2026. Pin fetched versions/hashes at implementation. These establish mechanisms/interfaces, not promised savings on the owner's repositories. Prior discussion's quantitative claims are intentionally not reused as verified experimental evidence.

- **Context:** user-supplied “Review LLM Coding Agents” conversation, ID `6aeae5fa-e318-83eb-8713-49a848f0e126`, retrieved five turns including Adaptive Context Optimization and VISTA-Memory reviews. Original attachments unavailable.
- **O1:** [Official non-interactive Codex documentation](https://developers.openai.com/codex/noninteractive): CLI execution/JSONL. The exact provider/account capabilities still require local audit.
- **O2:** [Official hooks documentation](https://learn.chatgpt.com/docs/hooks): lifecycle feedback and diagnostic model-request hooks; check current semantics and installed release.
- **O3:** [Official Codex MCP documentation](https://developers.openai.com/codex/mcp): connected tools and configuration, not arbitrary context mutation.
- **O4:** [Official API prompt caching guide](https://developers.openai.com/api/docs/guides/prompt-caching): model-specific caching and usage/cost categories; not subscription invoicing documentation.
- **R1:** [ReasoningBank paper](https://arxiv.org/abs/2509.25140): reusable experience-derived strategies, including failures. This spec does not implement its separate test-time scaling mechanism.
- **R2:** [Agentic Context Engineering paper](https://arxiv.org/abs/2510.04618): generation/reflection/curation and evolving structured context. ACE here means Agentic Context Engineering, not other projects sharing the acronym.
- **R3:** [LCM project/paper entrypoint](https://www.losslesscontext.ai/): hierarchical summaries with accessible underlying material. The specification uses the architecture concept, not a claim of a supported native Codex compaction connector.
- **R4:** [Mem0 OSS overview](https://docs.mem0.ai/open-source/overview): self-hosted/library deployment and configurable inference/storage components. Pin actual OSS version/features and do not assume historical managed benchmark parity.
- **S1:** [Supabase vector columns](https://supabase.com/docs/guides/ai/vector-columns): optional pgvector architecture.
- **S2:** [Supabase Storage access control](https://supabase.com/docs/guides/storage/security/access-control): optional private-object policies.

Evidence classifications in audit/report: `owner_requirement`, `retrieved_prior_discussion`, `official_documented`, `locally_verified`, `research_inspiration`, `proposed_design`, `unverified`. A proposed API in this specification never becomes a documented Codex feature by being implemented in the harness.
