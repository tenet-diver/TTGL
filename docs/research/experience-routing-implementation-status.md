# Observatory experience routing: implementation checkpoint

Updated 18 November 2026. Resume from this file and the current `AGENTS.md` before
editing. The complete user-supplied specification is preserved in
[experience-routing-plan.md](experience-routing-plan.md). The implementation and
registration guide is [experience-routing-001](../../experiments/experience-routing-001/README.md).

**This is an unfinished implementation checkpoint, not a completed experiment.**

The latest continuation is documented at the end of this file. It advances the
runtime/replay implementation, resolves tested subscription-binding failure modes,
and passes **48 Python tests plus 82 web/database tests**. The earlier 17 November
counts and process paths below remain historical receipts. No new model calls,
benchmark grades or economic results have been produced.

The user requests continued implementation and eventual evidence-backed results,
and requested this checkpoint before pausing. All new model execution remains
disabled. No new scored Luna/Sol trials, annotation audit, transfer experiment,
calibration, or benchmark reservation has occurred. Scheduled monitoring is paused.

## Completed work

| Area | Implemented and inspected | Remaining qualification |
| --- | --- | --- |
| WP1 inventory | 246 historical manifest/protocol sources inventoried; 127 prior/reserved task IDs conservatively excluded; no active research queue owner detected at inventory time | Source-specific provenance/permission audit before selecting actual seed traces or fresh tasks; alias/chronology audit |
| WP2 contracts/storage | Strict additive v3 sidecars over accepted v2; immutable scoped versions, predictions, support links, snapshots, records; PostgreSQL FKs/indexes; derived ClickHouse outbox; exact local S3 retention | Broader migration/real-data stress review; no destructive migration |
| WP3 annotation | Separate finite source-bound tool-disabled Luna base-v2 and envelope-v3 jobs; bounded inputs; no retry of started/uncertain calls; retained outputs/usage; candidate/public support admission guards | Real finite native qualification and 60-trace audit; large-trace block orchestration/reconciliation beyond the deterministic block helper |
| WP4 retrieval | Eligibility before ranking; source-version freshness, project/study/arm/split/watermark/exclusion/chronology checks; lexical search; pinned optional vector query path; bounded packets, cache and receipts | Optional embedding runtime/pgvector qualification; optional Luna applicability reranking is disabled and not implemented as a running job; explicit compact parent expansion needs review |
| WP5 plans/checkpoints | DAG validation/readiness, immutable plan revisions, cumulative source snapshots, untracked files/modes/symlinks, restore and independent replay, protected-write admission | Qualify actual actor image, tools, environment/source identity and native memory/mount canaries |
| WP6 delegation | Retained invocations, role accounting, empirical public-reuse router, small/large routes, one public fallback from restored checkpoint, public checks/integration, final whole-task checks, quarantine on uncertainty | Native end-to-end trial; broader runtime edge cases; final integration failure/replan policy review |
| WP7 benchmark boundary | Allowed-field projection, exposure exclusions, separate pinned existing evaluator adapter, sealed patch manifest, zero-test grade rejection | Real official/pristine empty/reference and candidate replay gates before benchmark scoring |
| UI | Experiences, Delegation, Experience results pages use shared DataTable; study scoping and evidence inspectors | Desktop dark browser suite passes; native trace-to-result drill-down requires actual qualified trial |
| Experiment CLI | inspect, validate-config, inventory, build-splits, prepare, annotate, audit-annotations, replay-subtasks, calibrate, freeze, run, grade, report, fixture | Real manifests/pins/budgets and evaluator adapters need native qualification; serial reference runner deliberately rejects concurrency registrations |

The later controlled studies, online accumulation campaign and concurrency/specialist
extensions (WP8–WP11) have not run. Online barriers and lineage checks exist in the
service; the actual sequential online publication driver still needs qualification.

## Retrieval and routing design

1. Request-level retrieval runs in the experience service, initially PostgreSQL full
   text. The lexical baseline uses OR over normalized terms so a relevant procedure
   can match a plan node with different surrounding words.
2. A pinned large Sol planner produces a bounded DAG using public context and the
   request packet. LPM/SFM/HRM share one measured initial plan in the controlled study.
3. Every ready node retrieves from its authorized frozen snapshot. One recovery
   query is permitted after a relevant public failure. Identical queries are cached.
4. The host router uses compatibility and observed independent-parent **public
   integrated** reuse outcomes, uncertainty and expected total cost. Sparse evidence
   selects the large executor. Cheap-first/exploration arms have explicit identities.
5. Luna executes a selected small node; Sol executes large routes or a distinct
   registered fallback after public failure. Every fallback restores the full
   pre-node checkpoint, including accepted dependencies.
6. Deterministic public checks and integration run in pristine workers; final
   independent grading remains outside routing/admission. Source-bound tool-disabled
   Luna later interprets public traces and extracts candidate procedures.

No model self-confidence is presented as an empirically calibrated success
probability. No hidden grade enters live retrieval, routing or fallback.

## Validation receipts so far

Private raw logs: `work/security/experience-routing-001/` (ignored, do not commit).

- Web unit tests: **54/54 pass**, `web-unit-tests.log`.
- Existing plus new PostgreSQL/ClickHouse/S3 integration suites: **23/23 pass**,
  `full-integration.log`. The new suite contributes 7 tests, including all 11 new
  collections' filtering/sorting/pagination, lexical retrieval with changed query
  words, temporal/arm/lineage/chronology exclusions, immutable publication, stale
  source cache invalidation, native usage non-duplication and concurrent attempts.
- Python experience package: **18/18 pass**, `python-tests-004.log`, including
  cumulative deltas, native response deduplication, unknown usage, checkpoint
  restoration, protected writes, no retry, freeze drift and zero-test grading.
- Six deterministic edit/check/replay cases pass: success, public failure/fallback,
  integration failure/rollback, protected write rejection, uncertain call quarantine,
  budget exhaustion. Four successful artifact cases independently replay actual
  generated source. Backend is synthetic: **zero actual model calls**. Sanitized
  report: `results/experience-routing-001/mechanism-fixture.json`.
- TypeScript check passed (`/tmp/experience-typecheck-003.log`).
- Production webpack build passed (`build.log`), then app reactivated on **3333**.
- Desktop dark Firefox suite **33/33 pass**, including all three new routes,
  search/empty states, pagination, filtering, both sort directions, persisted
  queries, source/image retrieval, inspectors and reversible form/rule mutations.
  Receipts: `browser.log` and `browser/results.json`. No model calls.

Earlier failed software fixture/test outputs are retained privately and not
silently replaced. No new native experimental effect or economic result is known;
the 90% saving/observed quality-parity target is **unmeasured for this feature**.

## Runtime and storage

- Branch `work`; fetched `origin/work` before checkpoint, no upstream divergence.
- Base before these changes: `a21736be0be8b3ffafd7e2987503a81035e9ed20`.
- Production `http://127.0.0.1:3333`; synthetic test app `http://127.0.0.1:3433`.
- PostgreSQL 15432; ClickHouse 18123; approved local S3/SILO 13900.
- S3 test fixture 13990; reviewed Firefox WebDriver 14444. Check processes before
  starting another server/driver. Never stop unrelated Langfuse services.
- PostgreSQL migrations **006 and 007 and ClickHouse 002 have been applied to both
  production and isolated test databases**. They are immutable now: add a new
  migration for any schema change. Do not edit applied migration content.
- Node pinned runtime: `/usr/local/share/nvm/versions/node/v24.22.2/bin/node`.
- Root `node_modules` links to `/tmp/observatory-reviewed-web-20261116/node_modules`.
  `apps/web/.next` links to `/tmp/observatory-runtime-20261116/build`. Parent runtime
  node_modules symlink is required for webpack's resolution.
- Codex CLI **0.169.0** is installed; canonical source has ChatGPT auth token fields.
  No secrets were printed or copied into public artifacts. `tools/worker-mcp`'s
  95-package pinned SDK graph is **not currently installed**. Review before install.
- Existing actor image `ttgl-context-python:20261108-bash-001` was inspected only,
  digest `sha256:9ed8bd351e618aa9075306abee2a94a14954f35c23dbdc22902080e0dfbb930e`.
  A fresh full graph/base OS advisory review is not yet complete; no new actor was
  started. Do not mistake image existence for readiness.
- The installed Python JSON Schema/PyYAML closure was reviewed through fresh OSV
  (7 packages, zero findings). No new Python/web dependency installation occurred.
- User approves Garage as a vendor and asks for a reasonably secure artifact.
  Garage 2.5.0's previously confirmed findings are still unresolved; it was not
  started. Existing specifically approved SILO remains the local provider. Do not
  infer a blanket advisory waiver or substitute remote raw storage.
- Earlier authorized cleanup reclaimed **172.7 MiB** from verified disposable
  caches and compressed closed old memory snapshots, with restoration tested.
  Primary histories, database volumes, credentials and unique artifacts remain.

## Resume order

1. Read current `AGENTS.md`, this file, full plan and registration README. Inspect
   `git status`, actual process owners and receipts before invoking anything.
2. The browser suite completed **33/33 passing** before commit. Inspect the actual
   processes before restarting services. At checkpoint the isolated app wrapper PID
   was `197704`; production PID `197692`. Do not assume these PIDs remain valid.
3. Finish implementation review/tests before any native model calls:
   - Native `campaign.py` / `execution.py` / `backend.py` have model-free coverage
     but no actual native trial yet. Verify real CLI flags, MCP runtime readiness,
     stdout and full rollout capture, source binding, model support and metering.
   - Audit `campaign.py` failure paths (before/after invocation), global and per-
     parent budgets, shared-plan logical **token and latency** charges, complete
     inference cost centres and scenario-cost/resource-cap enforcement. Actual
     invocations and logical shared deployment costs are deliberately separate.
   - Check dynamic node repository-state hashes (the query helper currently starts
     from the assignment's initial hash), online watermark advancement, per-arm
     statistics and annotation publication. These need integration qualification.
   - Match replay freezes to checkpoint source hashes and restore **the exact node
     contract**. The replay manifest checks identities; the campaign adapter needs
     a direct replay qualification rather than assuming a fresh generated plan.
   - Ensure first-party public artifact/verification references are tied to the
     actual source work-item/attempt on extraction and admission. Candidates alone
     must not become delegation evidence.
   - Assess final whole-task public failure handling, bounded replan/fallback and
     durable terminal attempt state on cancellation/uncertainty. Do not reset
     consumed budgets by changing node IDs.
   - Add missing deterministic tests for these cases rather than claiming all 38
     proposed essential tests are already covered.
4. Complete model-free readiness and pinning. Draft config intentionally has null
   pins/budgets and `allow_model_execution: false`. Inventory and empty audit/replay
   manifests are **not** a completed corpus/reservation/annotation audit.
5. Register a small finite **new** native mechanism/preflight only after source,
   dependency, actor boundary, capture/metering and replay gates qualify. Freeze
   exact sources/prompts/models/rates/assignments and finite invocations/tokens/time.
   No started/uncertain call may be replayed automatically.
6. Prepare the actual public annotation audit and development checkpoint manifests;
   run their registered finite stages only after qualification. Keep all held-out
   benchmark reservations and old frozen studies untouched.
7. Publish measured native results with full cost/latency accounting and limitations.
   Do not call deterministic fixture passes model-quality or target90 evidence.

Useful commands (no installs or model calls):

```sh
PYTHONPATH=src python3 -m ttgl.experience_routing prepare --config experiments/experience-routing-001/config.yaml
PYTHONPATH=src python3 -m unittest discover -s tests/experience_routing -v
/usr/local/share/nvm/versions/node/v24.22.2/bin/node --experimental-strip-types --test apps/web/src/lib/*.test.ts
/usr/local/share/nvm/versions/node/v24.22.2/bin/node --env-file=apps/web/.env.test.local --experimental-strip-types --test apps/web/tests/integration.test.ts apps/web/tests/experience.integration.test.ts
```

Browser suite (reuse the existing reviewed driver; synthetic deployment only):

```sh
OBS_BROWSER_OUTPUT=work/security/experience-routing-001/browser-NEW_ID python3 apps/web/tests/browser_webdriver.py
```

Check production `/api/health`. To rebuild, stop only the owned Observatory Next
servers first, then run the pinned Node webpack build and reactivate using
`work/security/data-migration-20261116/activate-web.py`. Keep private runtime logs
under ignored `work/security`; public repository artifacts contain sanitized
manifests and aggregate software results only.

## Active continuation — 18 November 2026

Pulled `cdd00e2` on `work`; the pre-change Python experience suite passes 18/18.
This continuation is implementing and testing the checkpoint's remaining runtime
and accounting gaps. No model invocation, benchmark reservation, dependency install
or change to frozen historical generation sources has occurred. Execution stays
disabled while native readiness gates remain unresolved. Detailed validation and
remaining limitations will be recorded below as implementation progresses.

### Implemented and qualified in this continuation

- Native backend preflight checks the source account, executable pin and installed
  worker MCP runtime before an executor invocation. Every attempt resets its
  stream-retention state. Archival failures preserve parsed partial usage, private
  stdout/stderr and credential cleanup; no failed call is silently retried.
- Invocation deadlines are capped by both parent and campaign time. Actual campaign
  invocation/token/cost caps are separate from per-policy shared planner charges.
  Logical planner replay now includes its measured tokens, scenario cost and model
  seconds exactly once. Missing usage or pricing cannot satisfy an enabled cap.
- Campaign preparation, actor startup, last-assignment uncertainty and owned cleanup
  errors leave stop receipts. Uncertain or incomplete assignments do not become a
  completed campaign just because they are last in the assignment list.
- Parent attempts retain terminal records on cancellation, verification failure and
  ambiguity. Unknown public-check infrastructure does not trigger a model fallback.
  A final whole-task public failure is terminal in the reference policy and never
  overridden by successful node checks.
- Material node-failure replanning is wired into the delegated native campaign, with
  a measured large-model recovery invocation. The one-replan limit, original public
  criteria, accepted dependencies, failed/cancelled node states, lineage and consumed
  budget are preserved. Standalone arms do not acquire an extra planner.
- The controlled replay CLI now calls an exact-node adapter rather than the fresh
  parent-task planner. It restores cumulative source/dependency state and the exact
  original node contract. Empty, raw, structured-small and structured-large paths
  each execute one retained attempt; they neither replan nor publish shadow memory.
  Nonempty packets are rechecked against an authorized current snapshot. Raw packets
  also require a pinned audited public-provenance receipt. All four native adapter
  paths were exercised **with synthetic transport and actors**, not actual models.
- Source, shared parser, MCP bridge/lock and schema implementation hashes are captured
  by study freeze. Parent budgets are required alongside campaign budgets. Missing
  readiness manifests now expose their qualification gates in the preparation report.
- Native trace ingestion requires its registered invocation/task/arm identity.
  Outcome verification is restricted to the analyzed source attempts and exact work
  item. Matching evidence ownership is required; unrelated passing study checks are
  not a substitute for public support. Canonical ID mapping on real traces still
  needs native integration qualification before admitting a real supported corpus.
- Primary reporting retains unpaired/missing assignments in unresolved denominators;
  missing costs and invalid grades cannot produce a target90 success claim.
- Source archives use private checkpoint permissions. Failed actor startup removes
  the newly owned container. Existing frozen studies and generation files are intact.

### Subscription-binding repair

The reported generic binding failure had two reproducible implementation causes:
matching accounts stored under different collected Codex homes were rejected, and
unchanged source files could skip repair of missing turn binding metadata. Jobs now
resolve one available signed-in collected home for the **same account**. Different
accounts, API-key login and unknown ownership remain blocked. Unbound turns show an
instruction to configure their original source folder/home in Data list.

For an unchanged, previously retained source, the collector can reconcile missing
binding metadata after verifying its exact bytes against the retained archive hash
and parsing its native turn identities. It preserves prompts and unrelated metadata,
refuses cross-account reassignment, and invalidates cached task context. Already
healthy files do not get reparsed on every collection cycle. Migration **008** adds
the partial index supporting this lookup; apply it before restarting collection.
Explicit Codex homes are checked when saved, and collector login failures are visible.
This repair was tested with isolated retained sources; it is not evidence that a
separate user's running deployment has already been restarted or repaired.

### Current validation and next gates

Public receipt: `results/experience-routing-001/software-validation-20261118.json`.
Private logs: `work/security/experience-routing-001/continuation-20261118/`.

- Python experience tests: **48/48 pass**, including four replay subconditions,
  synthetic campaign execution, shared planning, uncertainty, real source editing,
  public verification, independent restoration, cancellation and bounded replanning.
- All current web unit/database suites: **82/82 pass**, no skips; an additional
  targeted binding regression run passes **5/5** after the final collector refinement.
- TypeScript and production webpack build: **pass**. Database tests use isolated
  PostgreSQL/ClickHouse plus the labeled local S3 protocol fixture.
- New dependency installations: **0**. Actual model invocations and new scored
  benchmark assignments: **0**. Scheduled research monitoring remains paused.
- No UI layout changed; earlier browser/deployment receipts are preserved and are
  not presented as current-host browser or real SILO/Garage compatibility checks.

Execution remains disabled. Remaining work is genuine native qualification and
experimental preparation: reviewed actor image and MCP graph, native source/model
capability and metering checks, exact replay pins, fresh public source/reservation
and 60-trace annotation audits, corpus/selection/rate manifests, positive finite
stage/parent budgets, and pristine empty/reference/evaluator controls. Optional
vectors/reranking remain disabled. The online watermark/publication scheduler and
per-arm annotation barrier flow still need integration qualification; do not call
this a completed longitudinal experiment or infer a savings/quality result.

A replay freeze's `replay` object must pin `checkpoint_manifest`, `node_contract`,
`original_plan`, and (for nonempty conditions) `experience_packet` and
`retrieval_query`, each as `{path, sha256}`. It also fixes condition, checkpoint ID,
contract hash, arm and `shadow_memory_publication: false`. Raw conditions pin
`raw_packet_provenance` with reviewed runtime-public visibility, exact raw evidence
hash and authorized source version IDs. The qualified runtime manifest must include
`replay_checkpoint_hashes` and the same checkpoint environment image digest.

This checkout uses the previously reviewed Node executable at
`work/security/next-migration-20261115/runtime/node-v24.22.2-linux-x64/bin/node`.
The earlier host's `/usr/local/share/nvm` and temporary symlinks are not portable;
verify the available reviewed runtime and owned processes on each environment.

Controlled replay should use its own registered study and distinct condition arms
for each checkpoint. Existing attempt ownership is immutable; a checkpoint/arm/node
slot already used in the parent study cannot be silently reused. Qualify the
replay study's eligible memory lineage and first-party source mapping before a
native run, rather than copying a primary-study token or bypassing its scope.
