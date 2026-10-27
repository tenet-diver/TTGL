# Does routing rescue small-model failures?

The current held-out fallback policy has not improved over standalone Luna.
The next experiment therefore measures rescue directly, rather than treating
low cost or availability of an expert as a positive routing result.

## Larger bounded comparison

The already reserved SWE-bench Pro V2 panel has 12 development and 24 disjoint
validation tasks, spanning repositories and languages beyond the original
Verified pilot. The population is 642 tasks; this is a subset study, not a full
benchmark score. Before any Pro inference, `routing-protocol-002.json` supersedes
the unrun four-arm prompt matrix while retaining its 48-development and
72-validation assignment caps.

Development arms are standalone Luna, standalone Sol, optional Luna-to-Sol
routing, and required specialist review. All share v3 common verification
guidance, tools, time and feedback access. The required-review arm makes the
candidate and checks first, then must send at least one self-contained handoff.
Noncompliance stays in the quality denominator and is reported separately.
Required review is a diagnostic control, not evidence of autonomous routing.

If required review rescues Luna failures and optional routing does not, the
observations implicate consultation decisions. If neither helps, inspect context
selection, the expert response and integration. These are diagnostic patterns,
not randomized causal identification of each component. Separate matched Luna
and assisted attempts may also differ through sampling.

To reduce this ambiguity, save the assisted run's exact patch immediately before
its first expert response. A temporary Git index includes staged, unstaged and
untracked source changes without modifying the actor's real index. Host records
outside mounted logs retain the authoritative patch and hash. After generation,
publish a derivative `agent/pre-handoff.patch` for the unchanged official
`PatchReplayAgent` using `patch_name=pre-handoff.patch`. Independently regrade
both initial and final patches on pristine images. No initial or final grader
feedback reaches the solving controller. A within-run recovery is observed
repair, not proof it could not have happened with another Luna-only attempt.

Report paired Luna-fail/Sol-pass cases rescued, Luna successes lost, consultation
on those cases, pre-handoff failures repaired, pre-handoff successes regressed,
missing snapshot grades and required-review noncompliance. Unknown cost or
snapshot evidence remains unknown. `handoff_metrics.summarize` rejects duplicate
or incomplete four-arm blocks, rather than selecting favorable attempts.

Run one complete development task block after the existing empty/reference,
actor boundary, native metering and pristine replay gates, then inspect measured
cost and runtime before expanding to 12 tasks. Freeze the optional policy before
the 24-task validation panel. Do not automatically expand validation if there is
no credible rescue benefit on development; separately register further prompt
development instead of repeatedly tuning on sealed outcomes.

## Implemented checks versus results

`RoutingDiagnosticCodex` is a maintained-Harbor agent extension, not a replacement
grader. Eighteen checks pass in the actual Harbor runtime with scripted model
fixtures, a real temporary Git repository, transport checks and paired-metric
examples. They cover shared guidance, required-review permissions, snapshot
timing/index preservation, post-generation replay export and full native-usage
propagation. Pro actor boundary and task-quality trials are still pending.

A separate live native context-only handoff check did execute Luna, Sol and
Luna integration: three calls and one consultation, with complete per-model
native usage and reconciled deltas. Luna sent its proposed clamp function and
observations; Sol identified an additional floating-point edge case; Luna adopted
explicit branches. Six post-hoc sandbox checks found five passes for the initial
proposal and six for the integrated proposal. This small required-review fixture
demonstrates actual message transfer and integration. It is neither a benchmark
accuracy result nor an autonomous-routing result. Its early invalid task metadata
was rejected before any invocation, recorded, and corrected without repeating a
model call. See `results/handoff-mechanism-001/validation.json`.

The running Verified study and its frozen policy remain unchanged. The Aider
test-feedback diagnostic remains a separate reserved panel, with its own
controls and verifier corrections. Neither framework tests nor toy mechanism
checks are pooled into task-quality tables or the 95/95 target calculation.
