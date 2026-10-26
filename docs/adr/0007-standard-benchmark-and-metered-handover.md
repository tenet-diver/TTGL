# ADR 0007: Standard-benchmark evidence and a metered Codex continuation

Date: 26 October 2026. Status: accepted for implementation; empirical conclusions
depend on the archived results. This extends ADR 0006 without replacing its
conversational research question.

## Decision

Use SWE-bench Verified as the primary public software-engineering benchmark.
Reuse its official task distribution and evaluator. Keep three distinct kinds
of evidence: previously recorded BugsInPy feasibility trials, a new analysis of
published SWE-bench agent outcomes, and future fresh, metered Codex trials. Do
not pool their task counts, costs or causal interpretations.

The public replay uses matched per-instance success and upstream estimated
inference costs from the official SWE-bench experiments repository. The primary
pair uses the same mini-SWE-agent release, with a ten-model portfolio as an
exploratory extension. Learn pre-task decisions on other tasks only; never use a
held-out task's resolution or realized cost to select its model. Include fixed
single-model policies, random routing, a declared policy grid and a clearly
nondeployable label-informed oracle. Freeze code, inputs and splits in the
results. Since source aggregates were inspected before selecting the study,
this is exploratory cross-validated analysis, not a preregistered confirmatory
trial.

The new Codex integration must generate patches from clean source revisions,
write official evaluator inputs, preserve failed assignments, refuse ambiguous
in-flight retries, and retain complete task/model/thread provenance. The
official grader determines resolution. Model self-reports never replace it.
Make task dependencies and worker/evaluator isolation explicit; a bare host
checkout does not recreate a benchmark container.

## Economic claims

Report cost per assigned task and cost per resolved task, including failures.
Upstream API estimates are a historical price scenario, not a present invoice.
Replay selection omits fresh collaboration, changing model behavior and some
deployment costs; add router-overhead sensitivity and disclose those omissions.
Do not report the oracle's savings as attainable or a replay policy's savings
as measured benefits of conversation.

For fresh Codex runs, collect native token counters and, where the account
supports it, backend-estimated thread credits. Keep API-equivalent cost,
provider-estimated credits/USD, allocated subscription expense and actual cash
expense separate. A fixed subscription fee does not fall merely because token
usage falls. Avoid double counting cumulative thread totals or parent/child
accounting. Missing data remain unknown.

The planned conversational claim still requires quality noninferiority within
three absolute percentage points and lower total cost versus the strong solo
agent. A 25% saving is the practical target. Report uncertainty and failed gates;
never choose the quality margin or successful operating point after seeing
held-out outcomes. A full 500-task benchmark is not automatically powered for
that margin, especially with correlated repositories and repeated attempts.

## Current execution boundary

The fresh native check in `results/codex-runtime-20261026/preflight.json`
recognizes ChatGPT authentication but fails before inference because the
inherited Codex state directory is read-only. It emits zero model events. Do not
change authentication files, remount protected directories, alter inherited
proxy settings or reinterpret this as zero-cost inference. The next live host
needs a normal writable Codex installation with supported authentication.

Finish the executable benchmark bridge, estimator, analysis, documentation and
handover in this checkout. Push them to the existing research branch. Preserve
external blockers and unrun experiments explicitly rather than marking them
complete. Use the handover to continue on a suitable host without rerunning the
old solved fixtures or guessing what was measured.

## Research contribution

Small models that route, delegate or converse with larger models have extensive
prior art, including agentic software-engineering work. The defensible master's
research contribution is reproducible cost–quality evidence and a controlled
test of persistent bidirectional conversation versus matched alternatives.
Novelty of a future positive result depends on its controls and measurement,
not the broad architecture or the title. Null and negative results remain valid
findings.
