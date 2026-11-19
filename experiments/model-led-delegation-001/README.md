# Availability, action similarity and experience recency

User steering, 18 November: the primary Codex agent chooses a bounded subtask and
calls a delegation tool. The tool checks for a qualified cheaper model, ranks
similar verified past actions and weights their age, then delegates or returns
`needs_parent`. The selected worker acts autonomously within its contract.
This refines the [model-led handover](../../docs/research/model-led-delegation-spec.md);
it is a different treatment from per-action RSI routing.

The current native design is [protocol revision 002](protocol-002.json): match
**typed subtasks**, supply grounded procedures, and attribute prior success to
the executor that actually performed the work. The original `protocol.json` and
earlier whole-task retrospective replay remain historical, separate evidence.

For the research topic on knowledge accumulation/generalization, the preferred
scientific schedule is [protocol 004](protocol-004.json) and its
[Codex accumulation study](../../docs/research/knowledge-accumulation-codex-study.md).
It reuses this tool and native harness, adds nested knowledge snapshots and
same-memory Luna/Sol controls, and keeps recency as a small secondary extension.
The snapshot/campaign extension is implemented; the main transfer run remains unlaunched.
Latest steering requires our independently implemented router against Luna,
Sol, FrugalGPT and RouteLLM; RSI is related work only. Earlier protocol003 is
preserved as a superseded proposal. Named released baselines need real compatible
adapters and development calibration; a public-check fallback is not FrugalGPT.

The Python implementation is `src/ttgl/model_delegation/` and adds no dependency.
The stdio MCP server exposes `route_subtask`, asynchronous idempotent
`delegate_subtask`, `get_delegation` and `cancel_delegation`. The queue is bounded
at four jobs with one active worker. Queued cancellation prevents dispatch;
active cancellation is a request, not a claim of instant process termination.
A bounded native call may finish; its artifacts/usage remain retained and its
terminal result records the cancellation. Owner restart never re-dispatches an
uncertain job automatically.
The `NativeNodeWorker` adapter reuses existing isolated native workers, raw
retention, public verification and metering. `serve` is route-only by default;
`--native-freeze` additionally requires the exact host-pinned freeze, qualified
receipt files, the same source account, retained local artifacts and positive
parent/campaign budgets. A durable campaign marker refuses automatic budget
reset on server restart. A blocked/uncertain attempt is not a passing result.

## Experiment

The [current protocol](protocol-002.json) compares the same parent/executor harness under:

1. Parent working alone.
2. Always use an available qualified cheaper worker.
3. Route using similar past actions and verified outcomes.
4. The same rule with exponential experience-age weighting.

Availability, admission and source/chronology exclusions apply in every arm.
The primary remains autonomous in defining work and integrating it. Tool routing
owns the final cheap-worker admission decision within the parent-authorized pool.
No additional routing model call is needed for this initial transparent baseline.

Recency is measured from actual execution/check time. Re-importing old traces
cannot make them new. Source-version invalidation, capability expiry and age
decay are separate checks. Both verified successes and failures are included;
repeated correlated steps cannot inflate the number of supporting parent tasks.
The weighted estimate is descriptive, not a calibrated success probability.

## Subtask similarity, guidance and past model success

Live queries now require `subtask_type`; optional `constraints` describe current
inputs/preconditions. The initial matcher weights subtask goal text, type,
constraint tags and actions. A similar parent task, or a different type of
subtask in the same project, cannot stand in for matching subtask evidence.
This is a transparent lexical/structured baseline, not semantic embeddings.

The tool distinguishes:

- **Independent cheaper-model success:** the same observed executor completed
  similar typed subtasks with verified public integration outcomes. No invented
  procedure is required to use those prior outcomes as support.
- **Success with retrieved guidance:** the same executor succeeded with specific
  versioned instructions. Admission requires a retained request/context reference
  and delivery of the matching applicable guidance versions within the packet
  budget. Recorded exposure does not prove the model followed the instructions.
- **Teacher examples:** successful Sol procedures can ground Luna's work but
  contribute zero observations of Luna competence.
- **Expert/human/unknown assistance:** keep provenance visible; do not count these
  as independent cheaper-model execution. Model self-reports and lifecycle
  completion are not verified integration outcomes.

Grounding includes a stable version ID, concrete procedure, preconditions,
acceptance criteria, source executor/assistance and linked verification evidence.
Unsupported advice is not forwarded as a verified procedure. Preconditions must
match declared constraints. Source visibility, chronology, version and lineage
guards apply to guidance and execution history. Missing old guidance does not
erase a known cheaper-model failure.

When only teacher guidance exists, the default evidence router returns
`needs_parent` and exposes that a guided trial is possible. The explicitly bounded
always-cheap qualification/development arm can bootstrap such trials; this is
exploration, not established model competence. Do not add an automatic unmetered
trial or claim that teacher success transfers without testing it.

A separate optional development mechanism comparison holds the Luna model,
subtask contract, checkpoint, checks and budgets fixed while presenting or masking
grounded guidance. It measures the value of instructions separately from the
routing decision. That native comparison is specified but has not run.

Parent MCP previews contain compact counts and evidence IDs. Detailed procedures
go into the bounded worker packet, so parent context does not grow with the full
experience library. Native host snapshot admission still must verify underlying
executor identities and evidence/context references before those records qualify.

V1 holds the worker packet's similarity ordering and byte budget fixed across
the two evidence-based arms; age changes admission, not prompt ordering at the
same time. A future age-ranked retrieval packet needs a separate ablation.
Check that the native seed corpus genuinely has age variation before claiming
this evaluates recency: inspect independent-parent coverage in <7-day, 7–30-day
and >30-day buckets. Do not fabricate old dates or treat new imports as recent
experience. If this gate fails, report the age question as unidentifiable.

Recency can simply reduce cheap-model coverage by weakening old support. Compare
development-selected similarity-only policies at matched cheap coverage/cost as
a secondary control, and report thresholds/frontiers rather than attributing
every quality increase to superior relevance. Tune half-life/thresholds only in
development. The eleven-task retrospective replay below is not that tuning set
or a confirmatory test; its default thresholds are kept unchanged.

Use the proposed 6-episode native qualification, 8/8 development pilot and later
eligibility/precision/budget-gated SWE-bench Verified holdout from the protocol.
Freeze age/score thresholds on development only. Include parent planning,
retrieval, worker failures, integration, cache reads/writes and final verification
in the cost ledger. No test-grade feedback enters live selection or memory.
Retain failure-inclusive paired task denominators, uncertainty and account/source
provenance. Actual native execution is not qualified in this checkpoint.

## Commands

```sh
PYTHONPATH=src python3 -m unittest discover -s tests/model_delegation -v
PYTHONPATH=src python3 -m ttgl.model_delegation prepare --output PRIVATE_NEW_PATH
PYTHONPATH=src python3 -m ttgl.model_delegation replay --root . --output PRIVATE_NEW_PATH
PYTHONPATH=src python3 -m ttgl.model_delegation serve --config PRIVATE_HOST_CONFIG
```

`prepare` reports gaps without invoking Codex or downloading anything. `replay`
uses only the 11 retained historical paired Luna/Sol task outcomes, with
leave-one-task-out evidence exclusion. This is an exploratory policy replay,
not a new benchmark or actual tool execution. Its assumed capability records and
whole-task lexical/outcome proxies do not qualify a native source or demonstrate
that retrieved subtask procedures transfer. Historical selected execution costs
exclude any new coordination overhead. New native studies remain disabled.

Private host config sets the immutable `context` (project/study/arm/account hash,
parent model, rate scenario, publication watermark and exclusions), reviewed
experience/model snapshot file paths, output root, optional policy values and
optional `native_freeze_sha256`. The caller supplies only task goal/action
features and a bounded contract; it cannot change source, time or publication
scope. Never place tokens or copied authentication in a config committed here.

Native integration still needs qualification: attach this server to the parent
Codex profile, map live experience/capability evidence into a frozen source-scoped
snapshot, and verify the parent's current workspace→worker checkpoint→returned
artifact→parent integration handoff. The tested adapter consumes an operator-owned
isolated workspace/check catalogue; it does not automatically install an MCP
profile, pull arbitrary collector history, or modify the parent checkout.
Parent-plus-worker accounting and a real task grade must be demonstrated together
before calling the native experiment operational. No UI wiring was added here.

The current collector account ID is absent in the managed credentials. No
qualified coding actor is installed, and there is no frozen native stage yet.
See the dated result/readiness artifacts for actual progress; fixture transport
and historical replay must not be presented as live Luna/Sol inference.


## Active native continuation

Finite qualification registrations005–018 preserve transport, actor, required
handoff, benchmark and public-annotation attempts, including failures. Results
are indexed in [the results directory](../../results/model-led-delegation-001/README.md).
The actual canonical subscription works. A patched offline Python actor and
reduced original official grader/parser namespace qualify the benchmark runtime;
full upstream evaluator dependencies remain blocked. Scope and security limits
are in [the reduced-runtime review](../../docs/security/router-reduced-runtime-20261118.json).

`reservation-016.json` reserves metadata/lineage-audited tasks without inference.
`preparation-017.json` owns the one sequential71-candidate empty/reference control
pass. Check its private actual state before continuation, never relaunch started
assignments. `stage-rules-020.json` freezes compatibility-based allocation and
baseline sufficiency/selection before main construction. The final scientific
split, source pins, finite native budgets and full test manifest must still be
registered before their respective stages. No heldout model calls have occurred.

Native released-method adapters use reviewed local hashing/linear features in a
separate numerical process. This is an explicit adaptation with real native
calibration still pending. Standard-library orchestration uses the existing native
Codex and local S3/PostgreSQL integration; the optional numerical runtime has its
own pinned graph and security receipts. Research schedules remain paused.

## Interruption recovery

[Recovery 030](construction-recovery-030.json) reconciles the completed
construction candidates from the original registration. The final registered
parent has an uncertain Sol invocation and an unrun Luna assignment. It stays
in the denominator and contributes zero records to the final planned prefix.
Development and held-out task memberships come from
[split 028](clean-split-028.json).

[Plan 033](observatory-development-plan-033.json) freezes three Observatory
evidence thresholds and the development selection rule before paired
development grades. It leaves execution behind the existing registration and
baseline sufficiency gates.
