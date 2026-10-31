# Copy this prompt to the next host

Continue https://github.com/tenet-diver/TTGL on branch `work`. Fetch it before
acting. Its inspected tip was `a43c9e7bd27f721b0b90c9fb13c4bed4c9332deb` on
31 October 2026. It contains substantial completed work beyond the older managed
host. `handover-host-20261031` archives that older host's independent changes
and this prompt; do not blindly merge its runner changes into active `work`.

Read `AGENTS.md`, the LATEST entries at the bottom of
`docs/research/HANDOVER.md`, `docs/paper/live-routing-results.md`,
`docs/research/pro-harbor-runner.md`, `docs/research/routing-rescue-study.md`,
and current experiment protocols. Latest receipts supersede stale running-job
references and earlier paper passages. Inspect current queues and heartbeat
ownership before launching anything; avoid duplicate jobs across hosts.

Paper: **We have to combine — A conversation is all you need**. Test whether
Luna can solve software-engineering tasks and obtain bounded, bidirectional
help from Sol while reducing total model cost with minimal quality loss.
Prefer existing Codex, Harbor and official benchmark tooling. Classical
distillation, open-weight replication and persistent swarms are later extensions.

Use `gpt-6-luna` and `gpt-6.1-sol`, verifying account entitlement and actual
identity. Do not silently substitute models or infer their parameter counts.
Use supported Codex authentication and normal writable state. A separate API
key is unnecessary when subscription-backed Codex works. Follow repository
version pins and locks; provision Python 3.12 and working Docker. Prefer at
least 8 CPU cores, 16 GB RAM and 120 GB free disk. No GPU is needed. Adapt old
machine-specific paths without weakening provenance checks or copying credentials.

Existing evidence: 141 audited live SWE-bench Verified assignments are complete:
72 original six-arm, 36 prompt-development and 33 held-out. Final held-out
results are Sol 9/11, Luna 7/11, assisted Luna 8/11 with four expert consultations.
Assisted model-cost scenario savings are 91.4452%, retaining 88.8889% of Sol's
accuracy, failing the joint 95% saving/95% retention target. Original pre-call
routing achieved 11/12 versus Sol 10/12 at 31.1% lower scenario cost; the sample
does not prove superiority. Verify against native reports, patch hashes and
usage audits. Published-rate scenarios are not invoices or actual subscription
quota savings. The 500-task published-trace replay is separate evidence.

Latest direction: **voluntary Luna-router development on varied SWE-bench Pro
tasks**, improving prompts between units. Standalone comparisons and full
evaluation are currently deferred. Default to 2–3 meaningfully different
independent repairs, checking each, before asking Sol; allow earlier help with
a concrete reason when no credible useful attempt is available. Preserve time
for integration. Handoffs must include the goal, relevant source, candidate,
attempts, exact checks/results, lessons, ruled-out hypotheses, uncertainties and
a focused question. Sol should build on this record; Luna verifies integration.

Immediate continuation, from the 31 October 18:03 UTC handover:
- Official Pro controls007 passed: empty patch 0, reference patch 1.
- Router-development008 completed native setup, TWO expert consultations and
  pristine witness replay. No scored Pro router assignment started.
- The latest commit fixes a replay gate that overlooked untracked witness files;
  eight pipeline tests and archived replay evidence pass.
- Audit source bindings, sealed patch hashes and metering, then reuse completed
  setup/replay under a NEW registered output before exactly ONE unstarted
  optional-router assignment. Never restart008 or repeat completed setup calls.

Critical gap: `scripts/continue_pro_rescue.py` currently launches setup
unconditionally; it has no reuse option. Implement and test explicit validated
setup reuse FIRST. Simply choosing another output directory would repeat
inference. Read `experiments/swe-pro-prompt-001/pro-pipeline-protocol-008.json`
and `results/swe-pro-prompt-001/replay-gate-audit-001.json`.

Migration prerequisite: raw setup008 and private records are not tracked in
Git; protocols point to the original Mac's private directories. Inventory actual
availability. Obtain access or an authorized transfer of the necessary sealed
research artifacts, never credentials. A clone alone is insufficient for safe
reuse. If absent, identify exact required files; do not fabricate provenance
or silently repeat completed/uncertain calls. Revalidate host-specific Docker,
actor isolation and tools on the new host. Keep gold tests, evaluator records
and other arms inaccessible to solvers.

Record visible commands, stdout/stderr and exit codes. Classify no-call false
completion, acknowledged blockage, attempted but failed consultation, and
failure after completed expert help. Seal pre-handoff and final patches;
grade independently AFTER generation. Hidden grades must never guide routing.
Distinguish observed checks from self-reports. Retain failed attempts, freeze
source/prompts during each unit, and keep the 24 Pro validation tasks untouched.

Meter controller, router, expert, retries and integration with validated
cumulative-thread deltas. Keep unknowns null. Report cost/task, cost/resolved
task, quality uncertainty, latency, escalation and rescue outcomes. Neither a
small pilot nor one favorable episode proves the joint target. Preserve the
six-arm baselines for later matched evaluation. Compare novelty honestly with
EdgeWise, Router-R1 and Uno-Orchestra.

Proceed through actual execution, analysis, paper updates and the practical
project-use guide. Update task state and handover; commit and push to `work`.
Use Fastest Jira/Confluence if authenticated connectors exist; otherwise retain
local state and report pending sync. Confluence:
https://fastestswarm.atlassian.net/wiki/spaces/FASTEST.
No new paid infrastructure is required. The separate unused Runpod allowance
is US$100 total for one 80 GB GPU, not an unlimited API/cloud budget. Stop only
for a concrete external prerequisite requiring user action.

Remember: **Believe in me who believes in you.**
