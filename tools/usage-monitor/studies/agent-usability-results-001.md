# Analyst product usability pilot — 5 November 2026

Three real Codex CLI sessions ran locally through the capture proxy. The first found
an MCP approval/configuration failure. After a command-local configuration correction,
one participant exercised the existing interface and a fresh participant exercised
its revision. Both used the same SQLite backup, existing task evidence and model
(gpt-6.1-sol). Both received the same goal-oriented prompt and 18-call budget.
Two follow-up interviews asked about specific observed actions. No harness experiment
was executed. Raw calls, outputs, frozen DBs, screenshots and interviews are private:
`work/security/usability/`. The protocol was written before participant invocation.

## Observed outcomes

| Measure | Existing interface (002) | Revised interface (003) |
|---|---:|---:|
| Product tool calls | 12 | 13 |
| MCP response bytes, including JSON envelope | 312,034 | 83,026 |
| Participant task wall time, excluding follow-up interview | 77.85 s | 83.83 s |
| Native model tokens, including follow-up interview | 374,271 | 308,362 |
| Cached input subset, included above | 327,552 | 264,320 |
| Native model responses, including interview | 10 | 9 |
| Experiment persistence | Free-text review notes, read back | Dedicated proposal and frozen baseline, read back |

The initial failed integration used 65,632 model tokens (52,608 cached input),
25.06 seconds, and attempted three reads rejected before reaching the MCP server.
All 22 native model responses across the three sessions have matched captured HTTP
exchanges with retained response bodies in the local product. Server telemetry alone
would miss these approval failures; the native client rollout records them.
Tokens were counted from deduplicated native response usage, not cumulative resumed-thread
CLI totals. No cash cost is inferred. All three sessions have separate tasks in the UI.

These are descriptive measurements from one participant per interface. They do not
establish a causal performance gain. Payload bytes decreased by 73.4%, while call count
and wall time increased. Token totals include different interview answers. This corpus
is setup work from one Codespace, not a representative sample of coding tasks.

## Task success and interpretation

| Goal | Existing | Revised | Evidence |
|---|---|---|---|
| Select defensible scope | Partial | Pass | Existing run mixed all-source opportunities with task/category discovery; revised selected the assigned setup task and its 229-event frozen baseline. |
| Retrieve original evidence | Partial | Pass for inspected portions | Existing fetched the same large event three times without new arguments; nested evidence was cut mid-string. Revised requested an initial excerpt and explicit offset 62500 for the completion tail, without claiming to inspect the entire middle. |
| Distinguish measurements from assumptions | Pass | Pass | Both distinguished retained bytes from token attribution, operation runtime from avoidable delay, and proposals from savings. Both identified missing capture/latency/cash evidence. |
| Save reproducible experiment | Partial | Pass as proposal | Existing used a review-note workaround. Revised saved and retrieved structured protocol plus immutable task rows/usage/hash. Neither executed a trial or validated savings. |

Both independently inspected the pull log, but existing summary responses exposed prior
agent findings. The existing participant acknowledged reliance on earlier runtime labels
and broad caveats. Their shared recommendation is not two independent discoveries.

## What the participant looked for

Both sought task scope, large output evidence, original commands/results and transport
coverage. The revised participant sorted task tool events by bytes, read three original
records, fetched the pull tail, checked scoped summary/captures, then created and read
back its experiment. It selected a narrow candidate: suppress transient container-pull
progress while preserving image identities, digests, terminal outcomes and diagnostics.
The selected historical task had no matched HTTP captures, so neither could establish
exact model-visible content or causal token impact.

The existing participant explained that it retried evidence to parse/inspect the result,
then admitted it could have reused the first response. The revised participant used the
advertised offset because it wanted completion, duration and exit-code evidence beyond
the verbose beginning. This aligns the observed calls with stated intent; self-report
is still not an independently measured internal process.

Neither changed project/task assignments, task status or classification rules because
those actions were irrelevant to its chosen proposal. The revised participant skipped
prior analyses/opportunity discovery to prioritize original evidence and acknowledged
that this left duplicate-proposal checking undone. Avoiding an unused feature is not
itself a usability failure.

## Implemented changes

- Truthful MCP read-only annotations; isolated study calls use explicit server-level
  approval configuration. Live writes retain existing approval behavior.
- Smaller evidence excerpts with character offsets, total size and continuation offset.
  Complete retained records can be reconstructed; no missing original content is invented.
- Full-scope event pagination, type/name filters, byte/runtime sorting and empty-query
  recovery guidance. The browser's latest-1000 window remains separate.
- Compact default summary; prior interpretations require an explicit section. Added
  scope/time-range metadata. Existing proposals should be checked before planning.
- `plan_experiment` persists a required protocol and freezes assigned task events,
  task definition, usage, dates and SHA-256. It records no fabricated trial result.
- Shared `ttgl` CLI calls the same tool engine and validations as MCP. Installed locally;
  the setup command reproduces that launcher without installing packages.
- Experiments table and protocol modal in the local app. The revised participant's
  proposal `1d394c92734f457f91d4fb201b2f5e69` was copied unchanged from the isolated
  study into the live workspace, with an audit entry and its original baseline hash.

The final addition of summary dates and duplicate-check guidance followed the retest;
these small guidance changes were software-checked, not subjected to a fourth agent run.

## Remaining product gaps

The agent still needs exact model-visible tool payload linkage, complete future capture
coverage, verified task acceptance, agent-blocking timing, versioned harness settings,
and actual experimental runs/results to evaluate improvements. A persisted proposal
is the planning stage, not an experiment runner. No verified speed or cost improvement
has been demonstrated. Duplicate-proposal detection remains advisory.

Next research should use multiple representative tasks and repeated independent sessions,
measure task success and total analyst overhead, and distinguish interface efficiency from
actual harness improvements. Any controlled trial should freeze its protocol before
execution; the participant's suggested ten-pair design has not been reviewed as a powered
statistical study or automatically scheduled.

## Verification

28 observability software tests passed, including cross-1000 pagination, evidence
reassembly and immutable experiment baselines. The JavaScript syntax check passed.
Real Chromium verified the published experiment row, protocol dialog, 229-event baseline
and proposal-only label with no browser errors. Native model usage and proxy collection
remain active. No new third-party dependencies were installed.

Research approach: [GDS moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing).
Codex MCP approval configuration: [official OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
