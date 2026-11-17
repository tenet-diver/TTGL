# Observatory experience routing 001

This registration currently qualifies software. **No new Luna/Sol coding trials,
annotation audit, or scored benchmark assignments have run.** Empty manifests
preserve that distinction. The full proposed campaign is in
[the supplied plan](../../docs/research/experience-routing-plan.md).

The additive implementation preserves the accepted v2 analysis. PostgreSQL stores
immutable sidecars, native source versions, snapshots, and receipts. Exact input,
output, native rollout, checkpoint, candidate and verification bytes are retained
in the configured approved literal-loopback S3 store before publication. ClickHouse
receives deduplicated derived facts; shared evidence does not duplicate native usage.

## Retrieval and model roles

1. The service retrieves whole-task/subtask procedures when a request arrives.
2. A pinned large Sol model proposes a bounded DAG and public acceptance contracts.
3. Each ready node queries the same authorized snapshot; a failure permits one
   additional recovery query. Repeated identical queries reuse a retained receipt.
4. A transparent host policy uses independent-parent public integrated reuse
   outcomes, compatibility, uncertainty and expected total cost. Sparse evidence
   defaults to the large executor. Registered cheap-first/exploration arms differ.
5. Luna executes selected small nodes. A public failure may start one distinct Sol
   fallback from the full pre-node checkpoint, including accepted dependencies.
6. Host-owned checks run in pristine workers. Final public whole-task checks and
   independent evaluator results remain separate. Unknown/uncertain calls stop.
7. Source-bound, tool-disabled Luna interprets retained public traces and extracts
   candidate procedures through explicit finite jobs. Public support requires host
   verification. Online statistics wait for terminal public publication barriers.

The shipped baseline is **lexical**, using PostgreSQL full text and bounded packets.
Hybrid vector retrieval accepts pinned normalized embeddings only after pgvector
and the embedding runtime are separately qualified. Optional model applicability
reranking is disabled in this registration; no unmeasured assessor cost is assumed.

## Commands

Run from the repository root with `PYTHONPATH=src` and the installed, reviewed
`experience-routing` optional dependencies. Model-free inspection does not import
the old numerical benchmark stack or install anything.

```sh
PYTHONPATH=src python -m ttgl.experience_routing inspect --config experiments/experience-routing-001/config.yaml
PYTHONPATH=src python -m ttgl.experience_routing validate-config --config experiments/experience-routing-001/config.yaml
PYTHONPATH=src python -m ttgl.experience_routing prepare --config experiments/experience-routing-001/config.yaml
PYTHONPATH=src python -m ttgl.experience_routing fixture --output /private/new-unique-fixture-output
PYTHONPATH=src python -m unittest discover -s tests/experience_routing -v
```

`inventory` and `build-splits` accept metadata only. `annotate` queues a finite list
of accepted v2 analyses; it makes no model call. The source-local worker executes
one exact retained job, requiring a frozen source-bound enabled study and explicit
`OBS_ALLOW_EXPERIENCE_MODELS=1`:

```sh
node --env-file=apps/web/.env.local --experimental-strip-types apps/web/scripts/experience-worker.ts PROJECT STUDY JOB_ID
```

`freeze` verifies all file/source pins, gate receipts and finite budgets; the draft
intentionally fails this gate. `run --config FREEZE_JSON --output PRIVATE_OUTPUT`
executes the exact serial assignment list. `replay-subtasks` executes four matched
checkpoint freezes with shadow publication disabled. `calibrate` consumes only
public development observations. `grade` invokes a pinned existing evaluator in
its separate private boundary. `report` computes paired failure-inclusive results
from independently graded rows. Every output identity is write-once.

The native runner requires an explicit balanced arm/task order, owned public source
workspaces, a qualified offline image and source-bound Codex runtime. It never pulls
an image or downloads a benchmark. The serial implementation rejects a concurrent
registration; capacities 2/4/8 belong to the later registered concurrency extension.

## Service and access

POST `/api/experience` uses `{apiVersion:1,projectId,experimentId,operation,payload}`.
Server `OBS_EXPERIENCE_PRINCIPALS` contains SHA-256 bearer token digests with project,
study, role, optional arm and task restrictions. The Python client reads
`OBS_EXPERIENCE_TOKEN` and permits only literal-loopback service URLs. Credentials
are never written into public manifests. Operator, runtime runner, source annotator
and public verifier roles have separate permissions. Runtime credentials cannot
publish/read evaluation summaries or access private grader storage.

Operations: `register-study`, `publish`, `snapshot`, `retire`, `search`,
`hybrid-search`, `read`, `plan`, `checkpoint`, `routing`, `attempt`, `attempt-event`,
`verification`, `reuse`, `barrier`, `artifact`, `artifact-manifest`, `embedding`,
`ingest-native`, `queue-extraction`, `job-status`, `accounting`, `readiness`.
`evaluation-summary` is operator-only and intended for sanitized owner-facing results.

Observatory exposes Experiences, Delegation, and Experience results under Optimize.
All record lists use the shared DataTable and retain searchable/filterable evidence
and exact identities in the inspector. Existing native analytics remain authoritative.

## Remaining experimental gates

Software checks do not supply an audited 60-trace corpus, empirical routing
calibration, model availability pins, fresh benchmark reservations, native actor
canary qualification, reference/empty controls, a price scenario, or statistical
power. Those records remain unresolved, so scored execution stays disabled.
No fixture outcome establishes model quality, transfer, latency savings or cash savings.
