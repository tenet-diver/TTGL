# Decision history across coding handoffs

The research question is **how knowledge accumulation and generalization
frameworks accelerate effective innovation outcomes**. This pilot asks
whether a fresh coding agent can use earlier engineering decisions to extend
existing code more effectively. Prior decisions are the knowledge, later
dependent checkpoints test transfer, and elapsed time alongside independently
verified progress measures acceleration. The pilot covers technical
problem-solving within the same project. It leaves cross-repository transfer
and broader innovation outcomes to later studies.

## Hypothesis

A fresh agent with access to earlier decisions and the conversations behind
them will pass more independently graded checkpoints, preserve more earlier
behavior, or finish comparable work faster. It may also lose time to searches
or follow outdated advice. A previous run's claim is evidence the next agent
can check against the present code and specification.

The intervention is access to predecessor history within a fixed task
sequence. One model and harness run throughout. A Luna-versus-Sol transfer
comparison and inference cost optimization are separate research questions.

## Related evidence

VibeMemBench finds that directly supplying verified earlier experience can
help some solvers, while most evaluated end-to-end memory-system pairings
did not beat their memory-off baseline. This makes it important to measure
retrieval behavior as well as benchmark outcomes. Here the history is the
actual earlier native session on the same checkpoint sequence and the model
chooses whether to retrieve it. [VibeMemBench](https://arxiv.org/abs/2609.23570)

## Benchmark

Use the first three checkpoints each of `l2m` (LaTeX-to-Markdown conversion)
and `cfgpipe` (command-line configuration resolution) from public
SlopCodeBench v1.0. This benchmark presents dependent requirements as
successive changes to the same implementation. Snorkel AI and HumanLayer
publish evaluations using it. The problem catalog is pinned at
`ba1f7fec544dae4ff274d2447d9b65aebfbc5196`. The
[fixture receipt](source-receipt.json) lists the exact input hashes and
existing grader package versions. [SlopCodeBench problems](https://www.scbench.ai/problems) ·
[Snorkel AI leaderboard](https://snorkel.ai/leaderboard/slopcode-bench/) ·
[HumanLayer replication](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/benchmarking-new-models-on-slop-code-bench.md)

The paired design and local native harness make this an adaptation of the
published benchmark. Report checkpoint test outcomes for these selected tasks.
Leaderboard scores use a different trajectory and harness setup.

## Matched handoffs

Checkpoint 1 creates one common source attempt per problem. Checkpoint 2 begins
from that attempt's source. Checkpoint 3 begins from checkpoint 2's baseline
source according to the rule fixed before inference. The next base never depends
on which arm graded better. Source attempts that fail still belong to the history
of the registered sequence.

Each comparison starts two fresh sessions at the same Git snapshot, with the
same public checkpoint specs through the current step, task prompt, installed
tools, pinned Codex CLI 0.170.0, `gpt-6-luna` at low effort, and 165-second native
invocation cap. Both use the same editable Python entry file. The baseline has
its repository snapshot and public specs. The other session also receives a
read-only Observatory history MCP tool. A common prompt makes history optional.
The matched artifact hashes and Git snapshot identities are verified.

| Problem | Checkpoint 2 order | Checkpoint 3 order |
| --- | --- | --- |
| `l2m` | Baseline, history | History, baseline |
| `cfgpipe` | History, baseline | Baseline, history |

There are four paired handoffs, eight continuation attempts, and two source
attempts. The outcomes are pilot evidence with two dependent lineages.
The grader runs the pinned upstream checkpoint cases and checks earlier
checkpoint behavior separately. Test definitions, expected outputs and
reference implementations stay outside the model workspace. The verifier
runs without external network access. The `cfgpipe` fixture service shares
a dedicated loopback namespace with the candidate. All six independent
reference controls passed and all six empty controls failed.
[Control inventory](control-inventory.json)

## Memory and search records

Use Observatory's local MCP server for this experiment. DeltaDB inspired the
combination of edit history and retrievable conversations. Following the local
storage decision, this pilot uses local SILO for raw retention and keyword
search over frozen predecessor bundles. The results measure this implementation
of history access. [DeltaDB](https://delta.dev/deltadb)

Each handoff has a frozen JSON array. Every entry includes:

| Field | Meaning |
| --- | --- |
| `id` | Stable ID of the predecessor attempt |
| `checkpoint` | Earlier checkpoint number |
| `summary` | The predecessor's structured report of decisions, alternatives and verification |
| `conversation` | A pageable projection of the recorded public prompt, messages, and shell tool actions and results |
| `source_event_sha256` | Digest linking the projection to its retained original event trace |

The raw native JSONL trace stays available in the approved local S3 store.
Only predecessor sessions from the same problem enter a bundle. The current
checkpoint's grader results never enter model context. A summary's claims can
be checked against the underlying tool records. The memory view does not
include hidden model reasoning.

The MCP `search` tool ranks eligible sessions by keyword matches. `read`
returns a selected summary or a page of up to 7,000 characters, with a
continuation offset for longer conversations. Each search or read has its own
immutable JSON receipt containing the arguments, returned data or error, output
byte count and local server runtime. The analysis counts searches, misses,
summary reads, conversation pages and distinct sessions opened. Native shell
commands and the raw conversation remain separately retained.

## Outcomes and interpretation

- **Primary outcome.** All upstream tests for the target checkpoint pass.
  Report both-pass, history-only, baseline-only and both-fail pairs, including
  runs where the agent ignores history.
- **Regressions.** Identify formerly passing earlier checks that fail following
  each continuation. Also report the overall number of target and earlier
  checks passed.
- **Efficiency.** Report elapsed native invocation time and measured native
  tokens per assigned run. Keep the local retrieval service runtime distinct
  from end-to-end agent time. No separate inference call creates the summaries
  or answers memory queries.
- **Mechanism.** Distinguish availability, search, opening a record, and use in
  a decision. Compare claimed influence with the retrieval receipt, relevant
  source evidence and the resulting diff. Identify irrelevant or misleading
  results alongside helpful examples.

The paired outcomes estimate the effect of offering history on these cases.
An agent's choice to search or read is observational. Treat trace-level
attribution as evidence for a mechanism, with uncertainty.

## Run and evidence

Execute from the repository root using the pinned locally installed Codex
binary selected in the study registration. Preparation downloads only reviewed,
pinned catalog files. It installs no dependencies.

```sh
python scripts/fetch_decision_history_fixture.py
PYTHONPATH=src python -m ttgl.decision_history qualify
PYTHONPATH=src python -m ttgl.decision_history run
PYTHONPATH=src python -m ttgl.decision_history report
```

The private root is `work/security/decision-history-scb-001`. Registration
freezes the source, inputs and expected order. Each invocation preserves its
pending, admitted and terminal receipts. An admitted call with no terminal
receipt requires reconciliation. The runner never automatically retries it.
Raw traces, retrieved content, grades and checksums have separate provenance.
The checked-in manifests contain only public fixture metadata and aggregate
evidence.

## Execution notes

The original run stopped after two calls because the collection boundary
rejected a candidate workspace after a syntax check generated a bytecode cache.
The retained tool receipts record two successful source edits. The recovery
reconstructed the source by applying the recorded literal text splice to the
recorded heredoc and independently graded the resulting exact bytes. This
recovery made zero new model calls. The original stop and terminal call
receipts are preserved.

Continuation 002 keeps the original prompt, actor, tasks, arm order, budgets
and grader. It verifies protected inputs and snapshots the designated Python
source, recording other workspace paths excluded from the submission. The
continuation uses the recovered source for its assigned baseline grade and
launches only calls without a prior admission.

```sh
PYTHONPATH=src python -m ttgl.decision_history run --continue-002
```

The continuation stopped during `l2m-c2-history`. Its saved candidate hashes
to the retained snapshot and passes 5/20 target checks and 35/52 earlier
checks in an independent replay. The paired baseline candidate passes 14/20
and 41/52. The interrupted history arm lacks a terminal receipt and complete
usage evidence. Preserve the snapshot grade as partial evidence and keep the
original paired outcome pending.

## Follow-up on individual decisions and conversation access

The follow-up memory server prepares a matched pair from a frozen handoff
bundle. Both arms can search and read the same session summaries and individual
decision records. The full-history arm can also open conversation pages. Search
uses the common summaries and decisions in both arms. Compare fresh Luna
sessions under the same parent snapshot, public specs, prompt, effort, tools,
time cap and independent grader. The original pilot estimates the effect of
offering history as a package. This pair tests the added value of opening the
conversation.

Save optional decision declarations as a JSON object under `work/security`,
keyed by eligible predecessor ID. This example shows an unverified decision.

```json
{
  "l2m-c1-source": [
    {
      "decision": "Preserve output order",
      "rationale": "Order is visible to callers",
      "alternatives": ["Sort output by key"],
      "applies_when": "The public format preserves source order",
      "check_item_id": null
    }
  ]
}
```

Use the `item.id` of a completed public `worker.shell` check from the cited
predecessor's retained `events.jsonl`, or leave it null for an unverified
decision. Preparation checks the trace digest and records the exact event line,
command and result digests, exit code, timeout state and bounded output
previews. The link establishes what ran and what it returned. The decision's
rationale and applicability remain attributed judgments. Legacy bundles can be
served with their session summaries and an empty decision list.

```sh
PYTHONPATH=src python -m ttgl.decision_history_followup prepare \
  work/security/decision-history-scb-001 \
  work/security/decision-history-followup/l2m-c2-002 l2m 2 \
  --decisions work/security/decision-history-followup/l2m-c2-002/decisions.json
PYTHONPATH=src python -m ttgl.decision_history_followup codex-config \
  work/security/decision-history-followup/l2m-c2-002 summary-only
```

Omit `--decisions` when preparing a new bundle with only session summaries. Use
`full-history` in the second command for its matched configuration. Each
`codex-config` result is a JSON array of `--config` arguments for the isolated
Codex launcher. Preparation seals the two arm files and their common search
input in a private manifest. The summary-only process loads its own projection,
whose data contains no conversation field. Each MCP process writes its own
immutable search/read receipts under `retrieval/`. These commands prepare
inputs and configuration for a follow-up. They make zero model calls.

The trial runner uses the prepared views to run one fresh pair. Put the pilot's
registered Codex executable first on `PATH` and use its source subscription.
The runner checks both pins, qualifies the grader with empty and reference
controls, and uses the same Git snapshot in both arms. The workspace shell runs
inside the existing offline actor. The pair has a 165-second cap per invocation
and zero automatic retries.

```sh
PYTHONPATH=src python -m ttgl.decision_history_followup_trial \
  work/security/decision-history-scb-001 \
  work/security/decision-history-followup/l2m-c2-002
```

Read `trial/report.json` after both arms finish. It links each native outcome
to the exact candidate, independent target and earlier check results, usage,
elapsed time and retrieval receipts. A started call without a terminal receipt
blocks replay. Keep this follow-up separate from the original pilot outcomes.

### Transport diagnostic 001

Both native sessions finished and attempted one history search. Codex blocked
both searches at its approval gate before they reached the MCP server. The
summary-only assignment passed 8/20 target and 45/52 earlier checks using
78,131 native tokens. The full-history assignment passed 14/20 and 45/52 using
170,893 tokens. Those scores are a transport diagnostic. Trial 002 explicitly
approves the two read-only MCP tools and uses byte-identical history views
under a separate registration. Both diagnostic attempts, exact source and
reports are retained locally.

### Completed follow-up 002

The fresh Luna sessions started from the same Git snapshot. The independent
checkpoint 2 reference passed 20/20 checks and the empty control passed 0/20.
Both native calls reached terminal completion. Recorded elapsed time includes
local archival work in the native transport.

| Arm | Target checks | Earlier checks | Recorded elapsed time | Native tokens | Searches | Summary reads | Decision reads | Conversation pages |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Summary only | 0/20 | 0/52 | 23.66 s | 71,887 | 2 | 1 | 1 | 0 |
| Full history | 7/20 | 37/52 | 151.02 s | 266,005 | 1 | 1 | 1 | 0 |

Both sessions opened the same predecessor summary and chose different decision
records. The summary-only session read a check-linked record, then twice sent
`timeout_seconds: 10000` to a worker that accepts 1–30 seconds. The worker
rejected both calls and the session ended with the original stub. The
full-history session read the unverified decision about processing order and
reported using it alongside the public specification. It produced a partial
implementation and opened zero conversation pages. Both assignments failed
full checkpoint completion. This pair establishes that live decision retrieval
works and leaves the value of opening conversations unresolved.

The audit reconciled terminal native token counts, retrieval receipts, candidate
hashes and independent replay of both target and earlier checks. The matched
report is retained in local S3 with the private artifacts under
`work/security/decision-history-followup/l2m-c2-002/trial`. Its SHA-256 is
`67b74ccffa46ee89f955c2349773edce398738736ecc7727b8540441e166d710`.
