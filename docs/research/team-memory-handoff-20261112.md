# Memory comparison handoff — 12 November 2026

The user requested this pickup record. The authorized scope is **finish the
active 56-run comparison and update its paper/results**. The user explicitly
excluded the older interrupted 80-run reservation from this continuation.
The existing queue is left running. No recurring research schedule is enabled.

## Read this before doing anything

At **00:03 UTC**, checkpoint038 contains **38 verified assignments: 37 passing
source artifacts and 36 normally completed parents**. Assignment039,
`tinydb-mcp_memory-1`, has an actual submitted turn and is unfinished at that
inspection. These are historical snapshot values; inspect current files and
processes first. A later checkpoint may already exist.

Private evidence root:
`work/security/codex-team-memory-extension-20261111/`.
Current study root: its `scored-001/` directory.

| Role | Current process at inspection | Entry/receipt |
| --- | ---: | --- |
| Sole generation queue | 598104 | `continue_team_memory_text_runtime_v8.py`; `continuation-007-started.json` |
| Attached final publication | 598863 | `finish_team_memory_study.py`; `publication-phase-started-006.json` |
| Own capture proxy | 588361 | `capture_proxy_native_routes.py`, loopback8452 |
| Own Neo4j launcher / server | 588400 / 588617 | loopback Bolt17687 |

The queue uses private **`scoring-config-011.json`**, SHA256
`0f0ec76b445a39217019b8cbc42decb1ac9393284f75ec1bbd0b3afc2ce7185a`.
It retains the sealed first32 attempts and invokes only the untouched suffix.
It freezes163 sources,11,046 runtime files and26 gate receipts. Tool execution
sessions were queue19472, publication58081, capture38607 and Neo4j37761; those
session handles may not survive a new chat/daemon. Process command lines and
immutable receipts are authoritative, not a PID or session number alone.

**Do not start a second queue, repeat a started/uncertain model call, restart a
publication or resume a schedule.** Never edit frozen generation/evaluation,
backend, startup, metering, continuation or analyzer source while this queue is
active. The read-only finalization/paper/plot helpers are outside that frozen
set. Check the actual configuration rather than guessing whether a file is frozen.

## Safe first inspection

Run from `/workspaces/TTGL`, branch `work`:

```sh
ps -eo pid,ppid,etime,args | rg 'continue_team_memory|finish_team_memory_study|capture_proxy_native_routes|Neo4jCommunity'
```

```sh
python3 - <<'PY'
from pathlib import Path
import json
r=Path('work/security/codex-team-memory-extension-20261111/scored-001')
for name in ['completion.json','stopped.json',
             'publication-phase-completed-006.json',
             'publication-phase-stopped-006.json',
             'publication-phase-failed-006.json']:
    p=r/name
    if p.exists():
        v=json.loads(p.read_text())
        print(name, {'assignments':len(v['assignments'])}
              if 'assignments' in v else v)
for p in sorted(r.glob('checkpoint-[0-9][0-9][0-9].json'),reverse=True):
    try: rows=json.loads(p.read_text())['assignments']
    except json.JSONDecodeError: continue
    print(p.name,len(rows),'source passes',sum(x['grade']['passed'] for x in rows),
          'normal parents',sum(x['parent_status']=='completed' for x in rows))
    break
PY
```

If active, monitor the existing worker. If stopped, audit the exact phase and
all already-started calls before considering a separately registered continuation
of untouched assignments. Finished grading/usage/archive work may be completed
without another model call. A verified pre-model preparation failure is distinct
from an uncertain/started call. Preserve every failed preparation/audit and
version any operational amendment prospectively. No automatic retries.

## Experiment and interim findings

The [protocol](../../experiments/codex-team-knowledge-001/memory-aware-extension-protocol-001.json)
crosses two reused development libraries, SimPy/TinyDB, with seven arms and
capacities1/2/4/8, one attempt per cell. Arms: native, notebook, official MCP
memory, Mem0/Luna, Graphiti/Luna, adapted Smallville/Luna, searchable visible logs.
Sol low codes; Luna does model-based memory maintenance. Every parent/child has
actual tool schemas and common publication/retrieval/revalidation guidance.
Stores are fresh and isolated by assignment; this is within-task cooperation,
not a longitudinal learning or held-out benchmark result.

Each cell has30 minutes,120 shared terminal calls, a4M observed team-plus-memory
token threshold and128 maintenance calls. Count in-flight overshoot; unknown
usage stays unknown. Source-only independent replay restores prescribed public
tests/resources: SimPy140, TinyDB200 non-skipped tests plus one optional skip.
Passing saved source and normal native parent completion are separate outcomes.

Snapshot038 has one source failure: assignment032, TinyDB/Mem0/Luna/capacity8,
stops at the token threshold;199 pass, one fails, one skips. The failure is
`tests/test_storages.py::test_read_once`, expected3 reads versus observed2.
The original source/grade are retained without repair, replacement or regrading.
Assignment005 also token-stops, with a passing saved SimPy implementation.

Matched timing reported to the user at checkpoint038:

| Arm | Matched runs | Run-end time / same-task, same-capacity native |
| --- | ---: | --- |
| Notebook | 4 | 0.75–1.28× |
| Official MCP | 2 | 0.98–1.10× |
| Mem0/Luna | 4 normal parents | 1.88–3.55× |
| Graphiti/Luna | 4 | 2.31–3.00× |
| Smallville/Luna | 4 | 1.35–3.07× |
| Searchable logs | 3 | 0.91–1.12× |

One additional matched Mem0 run is budget-stopped. These are interim individual
runs, with different available matched subsets, not pooled causal estimates.
Fully metered TinyDB/capacity1 scenario comparisons: Mem0 costs40% more,
Graphiti75% more; Smallville costs4% less but takes35% longer. Other incomplete
cost bounds frequently cannot identify a ranking. No observed accuracy gain is
established; finish the full matrix before interpreting final performance.

Rates are the frozen dated Standard-credit scenarios, **not cash, quota or full
deployment expense**. All recorded parent/child/Luna inference is included.
Cached/reasoning counters are subsets. Embedding/local/research expense is
additional and incompletely measured. No net economic saving is established.

## Operational history that must remain visible

- After12: native SBOM findings in Pillow13 bundled libjpeg-turbo/OpenJPEG stop
  the original runtime. A prospectively registered text-only FastEmbed0.9.1
  derivative excludes PIL/image APIs;14 text files/tokenizer ASTs are unchanged
  and eight recorded vectors reproduce exactly. Cells1–12 and13 onward remain
  labeled as separate dependency strata. A zero-byte checkpoint12 caught by the
  hold is preserved; reconstruction uses only sealed grade/audit evidence.
- Before actual13/20/21: container/service/transport preparations fail before
  task turns. Whole preparation histories and independent RPC/source proofs are
  retained. The startup client extends only one initialize/thread-start wait to
  120 seconds; inference transport remains unchanged. The service guard removes
  only an independently verified dead assignment-owned Unix socket. No started
  model call is repeated. Source quality is conditional on task-model invocation,
  not flawless first-launch deployment reliability.
- Cell27: native Graphiti parent completes and source seals; its broker exceeds
  the30-second shutdown wait. A zero-model helper completes the same source's
  replay/audit/archive. The graph export survives; one unfinished publication and
  unobserved service exit remain gaps. Amendment010 gives cells28 onward only a
  longer post-generation shutdown wait and explicit exit receipts.
- Cell32: the original audit refuses a still-active maintenance process. Once
  it ends, strict reconciliation finds two completed Sol captures absent from
  the stopped native transcript. Both audit failures are retained. Versioned
  auditorv2 counts55,228 positive provider-only tokens once, labels them as
  single-witness evidence and keeps native coverage/total usage incomplete.
  Total recorded cell usage is at least4,104,747 tokens. Original grade/source
  are unchanged. Amendment011 adds a bounded passive post-generation drain for
  already-started maintenance; it sends no signal, starts no process and grants
  no new coding turn. In-flight inference remains charged.
- The daemon restart happens after stopped32 and before preparation33. Own
  capture/Neo4j are restored from unchanged pinned artifacts and existing data.
  Other services and normal routes stay untouched. There is no recurring work.

See [research chronology](team-memory-extension.md), the amendment/finalization
chain004–011 and private history/recovery receipts. Frozen original source and
all negative evidence remain intact.

## Publication and remaining work

Current [paper](../paper/codex-team-knowledge/paper.md) remains a draft with the
completed24-cell pilot and new methods. The 80-cell interrupted reservation,
24-cell completed pilot and this56-cell comparison must stay separate.
[Appendix](../paper/codex-team-knowledge/appendix.md) contains real memory,
communication, empty retrieval, Graphiti baseline/MyPy caveat and failed-grade
examples with hash provenance. It also explains conditional Cognee admission
failures and why Qwen readiness failures do not rule out Graphiti/Luna.

The existing publisher waits on the exact queue process using a pidfd. After
actual56 completion, fresh subprocesses independently audit all source/runtime/
gate and archive member/link/XZ hashes; compute exposure/runtime/maintenance-role
counts; generate five SVGs plus self-contained HTML; update main-paper abstract,
results, discussion, conclusion, README and appendixG. It makes zero model calls
and cannot restart/retry the queue. If generation stops it exports only actual
progress. Wait for this publisher before editing its output to avoid overwrites.

After completion/publication, the next agent must:

1. Verify all56 ended, the final audit passed, and publication-phase006 completed.
   Inspect failed grades, parent stops, unknown/capture-only usage and missing
   operation receipts. Do not equate intents with completed memory creation or
   available reflection code with an observed reflection.
2. Editorially review the generated paper/appendix/README against actual data.
   Add a clear interpretation of matched performance and cost bounds. Preserve
   failures, runtime/transport strata, setup incidents and single-witness caveats.
   Fix compact numeric typography in generated prose where needed. Review
   limitations: two reused development tasks, one attempt per cell, fresh stores,
   public tests and no causal/held-out/longitudinal/cash-saving claim.
3. Validate JSON/CSV, local links, SVG/HTML self-containment and public privacy.
   There is no available browser/image renderer for SVG; structural fixtures
   passed. Do not claim visual screenshot inspection.
4. Regenerate `port-source-manifest-001.json` **last** with
   `build_team_memory_port_manifest.py`; the current146-file inventory is stale
   after later code/amendments and is explicitly interim. Include the static
   local import closure and notices. See [reproduction guide](../paper/codex-team-knowledge/REPRODUCING.md)
   and [migration-agent prompt](../paper/codex-team-knowledge/PORTING_PROMPT.md).
5. Do a scoped git review/commit/push if appropriate; authorization persists.
   Do not stage unrelated user changes or raw private evidence. No commit/push
   was made during this run. Report actual completed scope and key findings.

The finalization command is documented in REPRODUCING.md using config011. If its
publisher has already run successfully, do not duplicate it unnecessarily.
Public progress can be refreshed without models using
`analyze_team_memory_extension.py --root .../scored-001 --protocol
experiments/codex-team-knowledge-001/memory-aware-extension-protocol-001.json
--output docs/paper/codex-team-knowledge`.

## Environment, security and working tree

At this handoff, all **81 focused software checks pass**: the team-memory,
analysis, exposure, continuation, startup/socket, passive-drain and metering
tests, plus original native evidence/source-grade checks. These are software
checks, not additional scored model trials. Current public progress was refreshed
from checkpoint038 without inference.

Private raw evidence is ignored under `work/security/`; keep credentials,
captures, native homes, databases and service volumes out of tracked files.
At inspection the workspace has approximately770 MiB free, `/tmp`31 GiB. The
queue stops before new inference below128 MiB. Duplicate compaction of sealed
cells1–31 is verified against archive bytes; never remove unique/unsealed data.
Do not prune Docker, change live Langfuse services or delete user histories.

Reconstructible runtimes are under `/tmp/ttgl-team-memory-20261111/`, including
task runtime002, text-only-global002, own Neo4j/state, embedding assets and
`pygal-runtime-002`. They are not the sole durable copies of private evidence.
Pygal3.1.3/importlib-metadata8.7.1/zipp3.23.0 are the reviewed isolated plotting
runtime. The Matplotlib/Pillow wheel candidate and downloaded Pillow build
alternative were never executed and remain blocked. No new install is needed
to finish analysis. Codespace's incomplete-evidence exception is environment
specific; confirmed vulnerabilities still block affected artifacts.

Many study files are **untracked**, so HEAD alone cannot reconstruct the work.
The pre-existing dirty `docs/research/smallville-online-results.md` and unrelated
`repository_*`, `measure_repository_longitudinal.py`, `inspect_memory_artifacts.py`
and associated studies are user work outside this change. HANDOVER.md also had
pre-existing edits; append the new pointer, preserve everything else and do not
blindly stage the entire file. Scheduled monitoring stays paused.
