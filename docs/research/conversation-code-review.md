# Independent review of the conversational-agent experiment

Review date: 26 October 2026 (Europe/Amsterdam).

Scope: `src/ttgl/personal.py`, `src/ttgl/pilot.py`, their focused tests, the
frozen BugsInPy pilot grader and its protocol. This review did not change the
frozen protocol, grader, task checkouts or model submissions.

## Findings requiring attention

1. **Resumed controller identity needs the same check as the expert.** The
   reviewed orchestrator rejects a changed expert thread, but directly assigns
   `controller_thread_id` from each controller response. A resumed controller
   could therefore return a different thread and still complete the treatment.
   Before assigning that field, reject a missing or changed identifier when a
   controller thread already exists. Add a regression test that returns a new
   thread after expert consultation. This is an implementation issue in the
   standalone adapter; the live collaboration-interface pilot uses a different
   execution path.

2. **Audit actual evaluator trees before grading.** The frozen grader checks the
   task-manifest and grader-source hashes, but does not itself compare the
   current base and fixed-test directories against their recorded tree hashes.
   A separate pre-grading audit can enforce that integrity check without
   rewriting the frozen grader. During this review, all four base-tree hashes
   and all four fixed-test-tree hashes matched: eight checks passed.

3. **Separate artifact-policy failures from functional failures.** The frozen
   grader rejects every modification to a pre-existing test file, including
   additions that do not weaken an assertion. This is stricter than an ordinary
   interpretation of "preserve existing tests; adding tests is allowed."
   Preserve its recorded outcomes and expose the independently run functional
   test result alongside the prohibited-edit flag. Do not describe every such
   rejection as an inability to repair the bug. A future protocol should make
   the restriction on existing test *files* explicit and identical in every
   condition before execution.

4. **Do not label four issues as four independent samples.** Three selected
   issues come from tqdm, and two concern related truth-value behavior. The
   analyzer's `independent_tasks` label should become `assigned_tasks` or
   `task_count`; report two repository clusters. Its task-level bootstrap is a
   descriptive calculation conditional on this chosen task set, not evidence
   for generalization across independent repositories. Tiny or degenerate
   intervals cannot establish noninferiority or equivalence.

## Checks that passed

`python -m pytest tests/test_personal.py tests/test_pilot.py -q` completed with
**34 passed** at review time. These are software checks with scripted backends
and fake subprocesses, not model-performance results. They cover resumed
expert dialogue, clarification/challenge exchanges, malformed outputs,
unknown usage, prompt-router assignment, interruption refusal, duplicate-run
handling, resource limits and process-group timeout cleanup.

The orchestrator retains the same expert thread across follow-up requests. The
controller can act between messages, respond to a question or challenge, and
verify the final proposal. Unknown usage remains null when any turn lacks the
counter; dollar costs remain null. Failed and ungraded assigned trials cannot
silently disappear from the analysis matrix. An interrupted in-flight call is
not automatically repeated, avoiding unrecorded duplicate mutations or cost.

## Limits of what was verified

The standalone Codex CLI adapter has not completed a live authenticated model
trial in this environment; its nested app-server initialization encounters a
read-only filesystem. Mocked process tests cannot establish production endpoint
compatibility. The live pilot through Codex collaboration must retain its own
backend designation and model/condition records.

The expert's read-only sandbox and empty working directory are not complete
read-isolation boundaries. The code rejects several observed tool-event types
from context-only roles, and the runbook correctly describes remaining access
as an instruction-based restriction. A future confirmatory run requires proper
filesystem isolation and a more complete access audit. The shared environment
cannot prove that no agent could read another trial or its evaluator.

The protocol is a dyadic conversational study; it does not implement or test a
many-to-many swarm, learned delegation policy, adapter training or persistent
personal learning. The proposed cost-saving/noninferiority hypothesis cannot be
tested in dollars when usage and billing telemetry are missing. Expert-call
counts are a process measure, not an invoice estimate.
