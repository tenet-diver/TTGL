# General delegation policy: development specification

Status: proposed development policy, 2026-10-26. This is separate from the frozen study-001 prompts and results. No new model assignments have been launched under this policy.

## Objective

Maximize verified task success within the user's cost, time and risk constraints. Develop Luna's independent capability first, then measure the marginal benefit and cost of Sol assistance. Cheapest standalone inference is not the research objective. Model rankings are hypotheses to measure, not assumptions that every task must satisfy.

## Portable controller instruction

You own the user's task through completion. Work independently when you can make useful progress. A stronger specialist is available for bounded assistance; asking for help is an ordinary part of successful execution.

1. Identify the desired outcome, relevant constraints, uncertainties and a practical way to check success. Choose checks appropriate to the task: tests, source evidence, calculations, inspection, or user acceptance criteria. Distinguish missing information or tool access from a reasoning difficulty.
2. Make a bounded independent attempt when it can cheaply improve the result or produce evidence. Ask early if the task clearly exceeds your capability, a consequential uncertainty needs independent review, or an attempt would consume the resources needed for a useful handoff. Do not wait for failure as a prerequisite.
3. Reassess after meaningful evidence: a failed check, contradictory evidence, an unresolved assumption, or lack of progress. Diagnose the issue and try a materially different approach if it is promising. Repeated activity without new information is a reason to seek help. Confidence alone is not verification, and one expected failure during diagnosis is not automatically a reason to escalate.
4. Ask the specialist when its expected contribution justifies the remaining cost and delay. Choose a focused diagnosis, critique, plan, or delegated subproblem. Hand over the broader problem when the difficulty cannot be isolated. Follow the user's permissions and data boundaries.
5. Send a compact, self-contained handoff: goal and acceptance criteria; constraints; relevant facts and artifact excerpts; current approach or changes; attempts and their observed outcomes; exact failures or contradictions; unresolved questions; and the specific help requested. Separate observations from hypotheses. Include locations only when the specialist can access them; otherwise include the necessary content. Omit unrelated history and secrets.
6. Inspect the response, resolve disagreements using evidence, integrate useful work, and verify the result. Send new findings back when a follow-up can resolve a remaining issue. Do not treat the specialist's confidence as proof or repeat a request without adding evidence.
7. Finish when the outcome is adequately supported. State material unresolved uncertainty and unperformed checks. If tools, information, permissions or budget prevent completion, report that constraint accurately; specialist advice cannot substitute for missing access or authorization.

The controller can choose to act, gather evidence, ask for missing information, consult, or finish. Concrete budgets and tool schemas belong to the runtime configuration, not this general policy. Forced consultation is a separate mechanism check, not the default policy.

## Development and evaluation

Use a designated development set, spanning task types and difficulty, to improve independent solving, verification, stopping and handoff quality. The current study's observed cases are development evidence for subsequent policies; do not relabel them as an untouched final test set. Reserve fresh held-out tasks before selecting the final prompt.

Compare a strengthened Luna-only controller with the same controller allowed self-directed consultation, and a simple bounded cheap-first fallback policy. Keep solving and verification instructions identical where possible so improved prompting is not credited to routing. Compare one-way handoff and continued dialogue only when the data contain enough actual consultations. Do not require every task to consult merely to make dialogue appear.

During development, use published model benchmarks as external context and defer broad standalone reruns. Final performance-retention and cost-saving estimates need matched Luna-only and exact-version Sol-only controls under the same tasks, tools, effort, stopping rules and accounting. Published aggregate scores from different harnesses cannot supply the denominator for a causal retention claim.

Record independent attempts and observable checks before each decision, consultation reasons, handoff contents, specialist responses, integration checks, total tokens/cost scenario, latency and final independent outcomes. Distinguish failed task checks from infrastructure failures. Hidden evaluation outcomes must never trigger a live fallback or appear in a handoff.

Report the accuracy-cost frontier and paired task outcomes, including Sol-successes lost, Luna-failures rescued, unnecessary consultations, consultations that failed to rescue, and regressions after assistance. A failed nondelegating run is only a *missed opportunity* if a comparable Sol control succeeds; it does not establish that assistance would have rescued that exact run. Estimate rescue causally with a separately specified matched branch/checkpoint experiment if supported; do not silently replay failures or pick the best attempt. Report uncertainty and all development trials.

## Current evidence and boundaries

At the last inspected checkpoint, study-001 had 20/72 officially graded assignments. On its first three complete task blocks, Luna-only and Sol-only each solved 3/3; personal and reset-expert each solved 2/3. One-way consultation occurred once. These observations motivate better policy development but do not establish the model accuracy ordering or a delegation benefit.

Official model-selection guidance recommends comparing models on the same inputs and choosing the lightest setting that meets the quality bar: https://developers.openai.com/api/docs/guides/model-selection . Exact models in the current run are gpt-6-luna and gpt-6.1-sol. No comparable published paired results for this exact local harness have been established here.

## User target and decision rule (specified before the next study)

The user requests a 95% reduction in total model inference cost with at least 95% of matched Sol-only task accuracy retained. For a common task set, define cost ratio as sum(policy model cost) / sum(Sol-only model cost), and accuracy retention as policy resolved fraction / Sol-only resolved fraction. The joint target is cost ratio <= 0.05 and accuracy retention >= 0.95. An undefined denominator is not a success. Do not confuse 95% relative retention with a five-percentage-point absolute margin. Include all Luna attempts, router decisions, specialist conversations, retries explicitly permitted in the protocol, integration and verification model tokens in policy cost. Report tools, evaluation and deployment overhead separately; a token-rate scenario is not a measured cash bill.

Report paired uncertainty intervals and the number of Sol-success cases lost. Point estimates meeting both thresholds are preliminary when intervals cannot support the quality margin. A 12-case panel cannot establish a tight noninferiority guarantee. The target does not justify selective exclusions, outcome-driven test reuse or unrecorded retries. If no tested policy meets it, report the measured frontier and failure analysis; do not claim the target was achieved. Compare against strengthened Luna-only as well, since cheap independent success can make delegation unnecessary on easy tasks.
