# Smallville-style episodic memory: implementation and experiment plan

Updated: 8 November 2026 (UTC). Owner: active Codex chat.

Status: **plan was recorded before implementation; core implemented/software-tested; native canary registered, zero Smallville model trials so far**.
The user requests an implementation similar to the original, including its
prompts, storage behavior and ranking algorithm. All memory backends must be
**self-hosted and open source**. Paid/hosted memory services are excluded.
Authenticated cloud Codex inference remains the authorized experimental model;
that does not make inference free or local. Research schedules remain paused.

This plan extends the [experiment register](context-memory-experiment-progress.md).
It does not change frozen experiments, claim a winning policy, or authorize
repetition of started or uncertain model calls.

## Source fidelity and existing software

Primary references:

- [Generative Agents paper, sections4.1–4.2](https://arxiv.org/html/2304.03442v2).
- [Author repository](https://github.com/joonspk-research/generative_agents),
  pinned commit `fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4`
  (11 August2023), Apache-2.0. This is the original research implementation,
  not a maintained production service.
- [Released retrieval code](https://github.com/joonspk-research/generative_agents/blob/fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4/reverie/backend_server/persona/cognitive_modules/retrieve.py).
- LangChain's [time-weighted retriever](https://reference.langchain.com/python/langchain-classic/retrievers/time_weighted_retriever/TimeWeightedVectorStoreRetriever)
  supplies related ranking behavior, but is not the whole original system.
  Its [experimental package is being sunset](https://github.com/langchain-ai/langchain-experimental/issues/87).

Reuse reviewed local embeddings/storage/native metering rather than installing
an old simulation/Django/OpenAI dependency stack. The missing behavior is the
native-Codex adapter and traceable memory lifecycle, not a new vector database.
Prefer reusing isolated author functions/templates where their reviewed graph
permits it. Any small compatibility implementation must have source mapping,
parity checks, attribution and explicit differences.

The paper describes normalized recency/relevance/importance with equal weights,
LLM importance ratings, access-time decay and evidence-linked reflections. The
released `new_retrieve` currently uses additional weights `[0.5,3,2]`; its ordering
and defaults must be audited rather than silently replaced with the paper formula.
**Keep released-code and paper-described variants distinct.** Freeze exact primary
variant, clock, defaults and tie handling after source inspection and before calls.
The paper evaluates social believability; it does not establish coding savings.

## Implementation work and current progress

| ID | Component | What must be implemented / how | Status and evidence |
| --- | --- | --- | --- |
| S01 | Pin and inspect upstream | Fetch relevant subtrees/files at the pinned commit; verify Git blob IDs and SHA256; record license, source date and advisory/provenance coverage. Full recursive tree was truncated; use subtree reads, not an assumed complete inventory. Never execute the old whole stack. | Complete selected source audit: complete reverie subtree,21 selected files/templates verified. Full old stack excluded; selected fragments import stdlib only. See source-fidelity note. |
| S02 | Fidelity map | Map original observation/thought/plan fields, IDs, timestamps, access updates, embedding keys, importance, reflection depth and supporting-node references to the adapter. Read perception/storage/scratch/retrieval/reflection paths and their prompt callers. | Implemented mapping in original storage class plus adapter. Terminal perception/planner scope and restart semantics documented. |
| S03 | Original prompts | Preserve the actual importance/poignancy, focal-question and evidence/insight templates plus caller formatting and output parsing. Store licensed templates with hashes and source links. Keep native transport/output compatibility changes separate; do not rewrite social prompts into coding prompts in the primary variant. | Implemented:11 exact licensed templates; actual v3/v2 callers, wrapper and parsing mapped. Hash/source-fingerprint check added. |
| S04 | Durable memory stream | Self-hosted persistence for observations, reflections and plans with original-equivalent fields; retain raw evidence and exact IDs, namespace isolation and restart/replay behavior. Reuse SQLite/local files where compatible. No hidden tests, reference solutions, grades or operator commentary enter memory. | Implemented original JSON memory stream and snapshot/audit sidecar; software restart/isolation checks pass. |
| S05 | Embeddings | Reuse already reviewed pinned local BGE/FastEmbed runtime; no hosted embedding API. Persist model/source hashes and count embedding operations/loading/runtime. Clearly label replacement of the original embedding model. | Bridge implemented to reviewed pinned local BGE/FastEmbed; actual Smallville model/runtime canary pending. |
| S06 | Ranking | Port/reuse original normalization, cosine similarity, recency, importance weights, candidate inclusion, top-k and access-time updates. Log component scores, selection, exclusions and ties for each query. Audit paper/code differences and possible ordering surprises. | Implemented original function bodies; software checks preserve original weights/order/access updates. No efficacy result. |
| S07 | Importance scoring | Run original scoring prompt through authenticated Codex; preserve rating output and parsing errors. No hidden score informs salience. Include every scoring call in system inference cost. If batches/rules are later tried, register them as separate variants. | Original prompt/native callback implemented; actual scoring canary pending. |
| S08 | Reflection | Reproduce original trigger/accounting, focal questions, retrieval, evidence-linked insight generation and storage. Inspect upstream constants before freezing. Validate cited memory IDs; distinguish observations from inferred lessons. Count all reflection and derived-memory scoring inference. | Implemented original trigger/functions and prompt callbacks; stub threshold/evidence tests pass. Actual native reflection pending. |
| S09 | Agent integration | Expose memory write/search/inspection to the isolated terminal agent. Ingest only model-visible observations or explicit agent records; preserve an equal raw archive for controls. Store attempts, checks, lessons and uncertainties without fabricating verification. Do not change the global Codex installation. | Planned; existing native/Docker/MCP boundary still needs its actual canary. |
| S10 | Metering and traces | Link every scoring/reflection/reader response to the parent task. Reconcile native IDs, proxy and Langfuse; inspect actual retrieval/use. Preserve full decoded-redacted request/response evidence and immutable failures. | Shared capture/compaction prerequisites pass; per-call role registry/prompt receipts implemented for registered canary. Reconciliation pending inference. |
| S11 | Software/parity tests | Deterministic score/parity checks, access renewal, degenerate normalization/ties, embedding mismatch, namespace isolation, restarts, valid/invalid reflection citations and corrupted records. Test actual upstream-defined behavior before proposing corrections. |10semantic software controls pass with stubs; source/template fingerprint check added. Original loader warnings retained. |
| S12 | Native mechanism test | Fresh bounded canary exercises original prompts, real local embeddings, persisted writes, ranking, reflection and subsequent retrieval through Codex. Separate a deliberately triggered reflection mechanism check from a naturally crossed trigger. Register cap and failure policy first. | Registered/prepared smallville-native-mechanism001:6observations, expected41/max48calls; forced-trigger diagnostic explicit. Commit before launch. |
| S13 | Development comparisons | Run matched controls and ablations on development data/tasks; inspect actual memories and retrieval traces. Record losses and all creation/update costs. Nominate only by a frozen quality-and-cost gate. | Planned; no Smallville result. |
| S14 | Held-out comparison | Freeze selected policy and statistical interpretation before inspecting reserved validation task contents or outcomes. Complete the whole registered block; no favorable-subset stopping or post-hoc promotion. | Planned; six LHTB validation task contents untouched. |
| S15 | Publication | Maintain this table and experiment register; publish methods, exact prompts/hashes, variants, results, failures, cache/cost accounting and limitations in the scientific report and final export. | This plan published first; result sections pending. |

## Test sequence and gates

1. **Source and software phase, no model calls.** Complete S01–S06 and S11,
   enumerate graph/security evidence before first execution of any reused code,
   and compare concrete score examples to the pinned implementation. Test both
   persistence and ranking; a plausible-looking memory file is insufficient.
2. **Registered native mechanism canary.** Freeze source/template/runtime hashes,
   exact prompt substitutions, synthetic input, expected mechanical checks,
   maximum calls and zero automatic retries before inference. Exercise actual
   importance and reflection prompts and inspect the resulting memory stream.
   Forced-trigger checks are labeled diagnostics; they do not prove the natural
   trigger or task efficiency. No ambiguous call is silently repeated.
3. **Same-corpus ablation.** Use identical chronological evidence and local
   embeddings across relevance-only, original three-factor ranking, and ranking
   with reflections. Include raw files/notes and normal continued-context
   controls. Freeze future questions separately; never rate importance using
   future answers. Report retrieval evidence and cold-start/amortized cost.
   This isolates memory mechanics; it is not an official terminal benchmark.
4. **Long-horizon development.** First use the three already reserved LHTB
   development tasks: staged configuration repair, SQLite analytics
   reconstruction and coverage-guided fuzzing. Require each task's own
   empty/reference controls, artifact policy and native actor boundary before
   model assignment. Freeze actual arms/order/horizons/feedback before launch.
   Primary comparisons: normal continued Codex, files/agent notes, Smallville
   ranking without reflection, and Smallville ranking with reflection. Other
   memory backends remain separate registered comparisons, not a reason to delay
   the first eligible Smallville block indefinitely.
5. **Held-out validation.** After development selection, register the fixed
   candidate against matched continued and files/notes controls on the six
   reserved fresh tasks. Exact allocation, effect margin and analysis must be
   frozen before validation inference. Small sample limits remain explicit.

Use the actual configured task horizon and equal permitted public feedback;
do not stop after a convenient short episode or inject hidden grader failures.
For the currently running reference control,105 mandatory50-second rounds are
preserved. It is a harness control with zero model calls, not a memory trial.

## Outcomes, cost and failure analysis

Primary: independently checked task success and **total cache-weighted model
inference cost**. Include controller/reader, importance ratings, focal questions,
reflections, derived-memory ratings, summaries, retries, recovery and integration.
Report cached/fresh/output buckets per unique response. Native CLI completion
snapshots can exclude compaction: use deduplicated native response IDs, reconcile
auxiliary compaction, and never add cumulative snapshots.

Secondary: completed tasks per observed budget, task wall time, repeated failed
commands/hypotheses, stale or contradicted memory retrieval, relevant-memory use,
raw-evidence recovery, memory size and local embedding/database runtime. Similar
commands may be justified rechecks; repetition requires contextual review.
Importance is a model judgment, not calibrated correctness. Retrieval can
reinforce an incorrect memory; preserve evidence pointers and inspect that risk.

Apply the existing development nomination gate: retain every matched baseline
success, reduce total modeled inference cost by at least10%, and win a majority
of paired costs, with complete accounting. A passing small block is not proof of
population noninferiority. Failed quality or economics rejects promotion; it
does not erase evidence. A managed system is not a fallback: **no paid/hosted
memory services**, even if a free hosted tier is available.

Keep model-rate scenarios, actual subscription expense/quota, local compute and
full operational cost distinct; unknown amounts stay null. Research overhead is
reported separately and must not be described as recovered on first use.

## Update discipline

Update component status when code is implemented, checks complete, a trial starts,
a failure occurs or a result reconciles. Link the concrete artifact/commit; do
not mark implementation as tested or a test plan as model evidence. Append
versioned amendments before new inference, preserve frozen sources after calls,
and publish all negative and unexercised gates. Scheduled research remains paused.

### Implementation checkpoint,8 November

Core source and native/local callbacks are implemented after this plan was first
pushed in efeaa7a. See [source-fidelity map](smallville-source-fidelity.md) for
actual original behaviors and explicit adaptations. No benchmark efficacy claim;
native mechanism001 is prepared and must be committed before execution.
