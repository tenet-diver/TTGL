# Analyst-driven measured improvement — 5 November 2026

The analyst used the product to reach a **keep** decision for an optional Docker
progress evidence view after a registered comparison measured **45.58% fewer native
model tokens** with every quality check passing in all six runs. It first rejected
an earlier trial under its unchanged rule, proposed a coverage fix, inspected the
new measurements and actual compact evidence, and then reviewed accrued costs.

This is a useful improvement for the tested **log-diagnosis workflow**. It is not
proof of lower cost or faster completion for entire coding tasks. Development and
research have not paid for themselves on the first use.

## Actual matched comparison

| Diagnostic case | Raw tokens | Compact tokens | Raw seconds | Compact seconds | Quality |
|---|---:|---:|---:|---:|---|
| Historical successful pull | 101,795 | 50,372 | 22.94 | 16.53 | Both pass |
| Synthetic authentication failure | 101,920 | 65,858 | 24.24 | 19.52 | Both pass |
| Synthetic unfamiliar quota diagnostic | 102,428 | 50,382 | 21.13 | 18.74 | Both pass |
| **Total** | **306,143** | **166,612** | **68.32** | **54.79** | **6/6 runs** |

Raw had 304,565 input tokens including 190,848 cached; compact had 165,414 including
104,704 cached. Output was 1,578 versus 1,198. Cached input is counted once as an
input subset. Native response IDs are deduplicated. Product tool calls fell from
six to three; all retrievals and model inference are included in each arm.
Compaction took about 1–2 milliseconds per result. Wall time was 19.8% lower in this
sample; timing is descriptive, without a statistical/general speed claim.

The compact presentation retained about 4.8 KB from each 65 KB source by removing
2,011 exact-format transient layer progress lines. Image digests, terminal layer/image
outcomes, warnings, errors, unfamiliar lines and native source truncation warnings
remained. Both arms offered raw retrieval. Captured requests confirm that log content
actually reached the model. The client clipped the raw tool results further, so
server response bytes are not treated as exact model-input bytes. One observed raw
model-facing serialized tool output was about 42.7 KB versus 5.8 KB compact.

Five required checks per run covered exit status, all six pinned digests, incomplete
source coverage, next action, and diagnostic content. Six passes on reused development
fixtures are not broad quality-retention evidence. The failure variants are explicit
synthetic guards based on the historical success log, not observed real registry failures.

## Closed-loop analyst behavior

1. The original usability participant found repetitive progress in original evidence
   and saved a guarded experiment proposal through MCP.
2. The first registered replay (001) measured 406,043 → 177,054 tokens, but two raw
   runs missed the historical log's missing-middle warning. Its registered gate
   required every run in both arms to pass. We preserved that failure.
3. A fresh analyst queried the product, retrieved original evidence and recorded
   **inconclusive—do not adopt**. It recommended explicit completeness metadata in
   both arms of a separately registered trial.
4. Replay 002 added identical completeness metadata to both arms, retained the same
   compaction algorithm and fixed its decision rule before invocation. All six runs
   passed the quality checks and the registered 10% token-reduction threshold.
5. Another analyst inspected case-level results and tried
   `read_evidence(view="pull_progress")` against the original source. It recorded
   **keep**, limited to this replay and the optional evidence view.
6. A follow-up exposed the native research-cost ledger. The analyst retained its
   narrow keep decision but correctly distinguished repeat-use savings from the
   negative net result of one use and qualified amortization estimates.

Observed calls, native rollouts, full retained proxy exchanges, interviews, frozen inputs,
grades, model answers and screenshots are under ignored `work/security/`. The live app
shows both immutable trial results, the earlier inconclusive verdict, subsequent keep
reviews and the overhead ledger. All trial model responses have complete retained
captures linked by provider response ID. No automatic inference schedule was installed.

## Accrued cost and limits

Snapshot: **2026-11-05T19:41:33.927650+00:00**. Implementation is still active; this is a lower bound
through the recorded native responses, not a promise that all future costs are included.

| Native token component | Tokens |
|---|---:|
| prior usability research | 748,265 |
| implementation and supervision | 4,735,307 |
| both development trials | 1,055,852 |
| analyst evaluation | 545,727 |
| Current improvement research total, excluding prior usability | 6,336,886 |
| Including prior usability research | 7,085,151 |

Mean observed saving was **46,510.33 tokens per diagnostic case**. Dividing the current
accrued token count by that mean gives **136.2 similar repetitions**,
or **152.3** including prior usability research. This is illustrative
token-count amortization, not dollar break-even, a forecast, or a quota calculation.
Both arms of both development trials and analyst work are research expense. Human time,
cash subscription allocation and broader operating costs remain unmeasured. Historical
setup work predating these usability sessions is excluded. There is **no net first-use saving**.

Fresh independent task samples and actual coding-task outcomes would be needed before
claiming broad harness improvement. The original proposal's suggested ten-pair setup trial
has not run. No image pulls or running services were changed by the diagnostic replays.

## Use it locally

Open the app's **Experiments** view and inspect “Suppress transient Docker pull progress
in agent context.” Its original baseline remains 229 events/13,900,756 tokens; that is
historical task context, separate from the measured replay comparison above.

```sh
ttgl read_evidence --args '{"id":"EVENT_ID","view":"pull_progress","limit":"16000"}'
ttgl query_activity --args '{"section":"experiments"}'
ttgl query_activity --args '{"section":"experiment_accounting"}'
```

Raw remains the default and is available using the same ID with `view="raw"`.
This feature does not automatically modify ordinary Codex shell responses. The CLI
saved-log utility uses the same compaction algorithm. A post-trial CLI file-reading
fix preserves CRLF bytes; the algorithm is unchanged. Exact trial candidate sources
were recovered and checked against their preregistered SHA-256 hashes.

[Protocols 001](progress-replay-protocol-001.json), [002](progress-replay-protocol-002.json)
and [machine-readable aggregate results](progress-replay-results-002.json) are in the
repository. The pilot runner imports its measured results through an operator path;
MCP agents can append interpretations but cannot rewrite measured values. A keep verdict
is rejected when the registered gate fails.

Docker already offers [`compose pull --quiet`](https://docs.docker.com/reference/cli/docker/compose/pull/).
We evaluated that maintained option; the optional evidence view additionally preserves
retained progress for source-level retrieval and reports exactly which lines it removed.
No third-party packages or images were installed for these trials.

## Verification

32 observability software tests pass, including error/unknown-line preservation, idempotent
compaction, raw access, explicit coverage, immutable results and blocked keep verdicts.
JavaScript syntax passes. Real Chromium checked the measured percentage, keep verdict,
failed and passed trials, analyst notes and accrued overhead with no browser errors.
