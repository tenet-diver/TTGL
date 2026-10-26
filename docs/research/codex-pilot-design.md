# A controlled Codex personal-agent pilot

Status: planning rationale retained after execution. The frozen protocol and actual results are in experiments/codex-pilot-001 and results/codex-pilot-001; this document is not an outcome report. The purpose is to establish that the proposed cooperation can be executed and measured before making an expensive or statistically powered claim. This pilot does not validate an open-weight small model, local inference, learning from experience, or dollar savings.

## What can be tested here

The user authorized using Luna as the personal agent and Astra or Sol as an expert. The current collaboration interface can select these model identifiers and start independent conversations. It can execute real repository edits and tests. It does not expose a complete per-call input/output/cache token ledger or an invoice. Its model aliases and platform agent prompts are not immutable model checkpoints under the investigator's control. These limitations belong in the paper, not only in a runbook.

Use `gpt-6-luna` and `gpt-6.1-sol` for the first fully paired pilot. Add Astra only as a separately preregistered extension, rather than replacing a difficult case after seeing a result. Start every evaluated worker with `fork_turns="none"`; otherwise the worker inherits the investigator's literature, gold-patch knowledge and other arms' results. Select the same explicit reasoning-effort setting where supported and record the requested value. This is a setting match, not proof of equal internal computation.

## Reuse a public repository-repair dataset

The preferred compact source is [BugsInPy](https://github.com/soarsmu/BugsInPy), inspected at commit [`11c5f1eea954a42132cfd06bf257766a7963e0fd`](https://github.com/soarsmu/BugsInPy/tree/11c5f1eea954a42132cfd06bf257766a7963e0fd). It supplies genuine buggy and fixed repository commits, regression-test selections, Python versions and setup information. It is not a current frontier benchmark. It is a useful existing benchmark for an inexpensive repository-agent integration pilot and avoids inventing convenient tasks for this architecture.

A feasibility pool, fixed before any model trial, is:

| Project | Candidate BugsInPy IDs | Setup concern |
| --- | --- | --- |
| PySnooper | 1, 2, 3 | Python 3.8.1 in metadata; tracing behavior may depend on interpreter version |
| tqdm | 1 through 9 | Python 3.6.9, pytest 5.4.3, nose and old dependency pins |
| HTTPie | 1 through 5 | Python 3.7.3; several tests require HTTP fixtures |
| Cookiecutter | 1 through 4 | Python 3.6.9; old Jinja dependencies and tox configuration |

The first pool is inexpensive but contains many one-line fixes. It can therefore produce a ceiling effect and should not be selected to demonstrate the architecture's advantage. Use a prespecified feasibility order and take the first six distinct working instances. Determine eligibility by test infrastructure only: the designated regression fails on the buggy commit and passes on the fixed commit; a defined regression guard also passes on the fixed commit. Record every rejection and its reason. Freeze selected IDs, base revisions, test hashes, task text, interpreter, dependencies and command lines before spawning any evaluated model. Do not exclude an instance because a model failed it.

If an old test needs a compatibility adjustment, commit the exact adjustment, verify it on both buggy and fixed versions, and call the result an adapted BugsInPy pilot. A hand-written replacement regression is a new evaluator and must not be described as the official BugsInPy outcome. Gold patch size must not enter a router's features. Pin and record dependency versions, including an environment lock rather than only `requirements.txt`.

The SWE-bench Lite dataset metadata endpoint was accessible during inspection, but its parquet download redirected to a denied `us.aws.cdn.hf.co` host. The datasets-server rows endpoint was also denied. Those are environment access issues, not an argument against SWE-bench. The full study should use an official SWE-bench harness and a larger, stratified, sealed task panel once its images and datasets are available.

## Four arms with the same task contract

| Arm | Worker behavior | Purpose |
| --- | --- | --- |
| Luna only | Luna inspects, edits, tests and submits | Small-model control |
| Sol only | Sol uses the same tools, task and personal context | Large-model control |
| Prompt router | A fresh Luna sees only the task description and allowed metadata, chooses Luna or Sol once, then that fresh worker completes the task | Cheap pre-task selection control |
| Personal collaboration | Luna attempts the task, observes its own tests, may use up to two bounded Sol expert turns in one conversation, verifies and integrates the response, then submits | Test the local actor plus selective expert interaction |

The prompt router is not RouteLLM. RouteLLM's published pretrained model was trained for a particular model pair and distribution; applying it to Luna/Sol without appropriate development evidence would not constitute a calibrated baseline. A follow-up benchmark can reuse RouteLLM's implementation, fit on disjoint paired development outcomes, and freeze threshold selection before test evaluation. Include a random router at matching expert-call rate and an offline oracle only as diagnostics; neither is a deployed policy.

Keep the same personal-context file available to all arms. Give concrete constraints, such as supported Python behavior, dependency restrictions and public API compatibility. This controls memory access; it does not test whether persistent memory was learned. To test personal understanding itself, use a separate multi-session protocol with preference updates and independently scored retrieval, stale-memory correction and constraint adherence. Do not conclude that persistent personal understanding works from independent repair tasks.

The collaborator should decide whether and when to request help. A request contains its objective, observations, current hypothesis or patch, relevant constraints, and a specific question. The expert gets only the transmitted context and the explicitly authorized files; it returns advice or a patch. The Luna worker owns the final edit and verification. The investigator forwards messages verbatim and enforces caps; the investigator must not diagnose the bug, choose a better solution, rewrite requests or synthesize the final patch for the tested architecture. In particular, the root agent's intelligence must not become an unreported extra expert.

## Budgets and assignment

The frozen pilot uses a 240-second task deadline, including routing and expert wait. The root interrupts overdue workers and records polling slippage. There is no claim of an enforced equal token or terminal-operation budget. Charge expert work against the collaborating system's total budget. A consultation may not silently give that arm a second full budget. Count all executed attempts, failed calls, test invocations, retries and expert messages; report task-budget exhaustion as an outcome. If the platform cannot enforce or meter an exact operation cap, report the intended cap and violations, and do not call the experiment compute matched.

Randomize the order of arm execution within task using a recorded seed. Use independent copied repositories, not a shared mutable checkout. Permit the same public project tests and prohibit browsing the internet or git history for fixes. If the historical dataset lacks issue text, create a neutral behavioral specification from the observed failure before any model run, preserve its provenance, and disclose that task descriptions were adapted.

The executed feasibility panel is frozen at four tasks and four arms, requiring 16 primary attempts plus selected expert turns. One attempt per arm per task is sufficient for a wiring pilot but not for a reliable model comparison. A later powered study needs independent repetitions and enough tasks for the prespecified effect size, with task as the pairing unit. Fixing seeds does not guarantee deterministic hosted inference.

## Sealing and verification

Keep gold patches and the evaluation test material outside every assigned worker directory. Make the worker-facing directory a clean base checkout without `.git` objects that disclose the eventual fix. The evaluator checks the submitted code in a fresh copy, rejects edits to evaluation files and captures the patch and test logs. Run fixed and buggy controls in the exact same environment. Do not give hidden test feedback to a worker after its attempt is complete and then count a repaired retry as the original attempt.

All collaboration agents here share the filesystem. Directory separation and explicit instructions are therefore soft isolation, not a security boundary. A worker could read sibling directories or concealed tests if it violated its instructions. Record that limitation and inspect observable tool traces for violations. A publishable full run should use separate containers or equivalent sandbox isolation with only the assigned repository mounted and independent evaluator access. Lack of a recorded violation does not prove no possible information leakage.

## Measures and honest claims

The primary pilot measure is the paired number of accepted repository repairs under the frozen regression and guard tests. Also record elapsed wall time, observable tool calls, expert calls, handoff bytes, own tests executed, patch size, explicit constraint violations, completion status and infrastructure failures. If the platform exposes reliable final token counts later, retain the raw usage events and the exact rate card; do not estimate them by counting output characters.

Per-task dollar cost is **unavailable** in the present interface unless an authoritative usage ledger is obtained. Model-call counts, elapsed time and message bytes are process measures, not interchangeable cost estimates. Do not call a Luna/Sol mixture cheaper simply because Luna is described as smaller. Report hosted service latency as observed, including queuing and platform overhead, without interpreting it as isolated model inference latency.

Show the per-task outcome table before aggregates. With four tasks, a success difference of one task is 25 percentage points; uncertainty is very wide. Report paired differences and exact or bootstrap uncertainty as descriptive results, with no claim of frontier performance, superiority, noninferiority or generalizable cost savings. Analyze infrastructure failures separately and retain an all-assigned outcome. A failed cooperation arm is a useful result; changing caps, prompts or selected tasks after observing it creates a new pilot version.

The four-capability architecture is broader than this first pilot. Editable personal memory, adaptive delegation policy learning and persistent many-to-many cooperation each need separate interventions, controls and longitudinal measurements. The present experiment tests only whether a small acting agent can use a bounded large expert effectively on real repository repairs under a common interface.
