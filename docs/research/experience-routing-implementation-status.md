# Observatory experience routing: implementation checkpoint

Updated 17 November 2026. Resume from this file and the current `AGENTS.md` before
editing. The complete user-supplied specification is preserved in
[experience-routing-plan.md](experience-routing-plan.md). The implementation and
registration guide is [experience-routing-001](../../experiments/experience-routing-001/README.md).

**This is an unfinished implementation checkpoint, not a completed experiment.**
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
