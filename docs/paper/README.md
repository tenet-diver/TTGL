# We have to combine — A conversation is all you need

**Using small language models as conversational routers for agentic software engineering.**

Working previews: read the [PDF](paper.pdf), edit the [Word document](paper.docx), or open the
[self-contained HTML](paper.html). [Markdown](paper.md) is assembled from the
chapter sources. This is the active paper; the [earlier thesis](../thesis/README.md)
remains a supporting literature and design supplement.

The hypothesis is materially lower **total cost** with a small, registered
performance-loss tolerance. The controller and expert can clarify, challenge
and revise across a continuing conversation. Personal memory, learning and
multiple experts are optional extensions. Router-R1, EdgeWise and related work
already cover much of the architecture: this is a replication and controlled
extension, not a first-invention claim.

The paper contains a full related-work review, system design, paired experiment
protocol, economic accounting, live pilot results, a complete SWE-bench Verified
replay, limitations and next-study design. The proposed confirmatory gate uses a three-point quality margin and a
25% practical savings target; neither is established by the pilot.

The latest [fresh metered routing results](live-routing-results.md) cover 72
original assignments and 36 prompt-development assignments, with
[cost–performance graphs](../../results/prompt-comparison-001/README.md).
Improved adaptive and cheap-first prompts reached 4/4 development successes,
matching Sol at 87.1% and 89.1% lower model-cost scenarios. These are development
results. The completed [eleven-task held-out study](../../results/delegation-heldout-001/analysis-002/README.md)
resolves 7/11 with Luna, 9/11 with Sol and 8/11 with assisted Luna. Routing rescues
one Luna failure and loses no Luna success, with four expert consultations.
Assisted savings are 91.45% and accuracy retention is 88.89%; the joint 95/95
target fails. All 33 assignments passed independent native usage and official
patch/grade audit. One invalid independent control was excluded before inference
without replacement. The earlier interim checkpoints remain archived.
Generated working previews have been rebuilt from these results. All 55 PDF pages
and all 43 Word pages have visual review recorded in
[the QA receipt](../../results/paper-preview-qa-011/receipt.json). The bounded Pro
study remains pending; these are not final research deliverables.

The [verification-feedback study](../research/verification-feedback-study.md)
adds a separately versioned policy candidate and a 12-development/24-validation
Aider-derived reservation to distinguish responding to test failures from
anticipating hidden failures. It has no model-quality results yet.

The [routing-rescue design](../research/routing-rescue-study.md) now governs the
unrun Pro comparison: matched standalone controls, optional consultation and
required review, with independent pre-handoff/final patch grading. A live native
context-only handoff check demonstrated actual review and integration, but does
not establish benchmark accuracy or autonomous routing.

The [prospective learning study](learning-study.md) specifies separate training,
development and evaluation data; observable trace collection; sequence and
probability distillation; RL; local/remote controls; and inference versus
amortized training-cost learning curves. These are planned comparisons, not
training results. The immediate priority remains the proprietary routing study.

| Live condition | Functional success | Accepted under strict artifact policy |
|---|---:|---:|
| Luna only | 3/4 | 3/4 |
| Sol only | 4/4 | 4/4 |
| Task-only prompt router | 4/4 | 2/4 |
| Optional conversational controller | 3/4 | 0/4 |

The strict policy rejects changes to existing test files, including added
assertions. All optional conversational controllers chose zero consultations.
The router always selected Luna. A separate required two-round dialogue passed
30 regression tests. These are tiny feasibility observations; **no savings or
noninferiority claim is supported for the live conversation**, and its token/dollar costs remain unknown.

The new [standard-benchmark analysis](standard-benchmark-results.md) covers all
500 SWE-bench Verified tasks and ten published mini-SWE-agent runs. The primary
learned router saves **46.1% estimated inference cost**, but loses **8.6 quality
points** (64.2% versus 72.8%), failing the declared quality target. MiniMax-M2.5
alone reaches 75.8% at about $0.073/task, illustrating why inexpensive strong
single-model controls matter. Historical replay costs are not measured Codex
quota savings or a live conversation result.

- [Prior-art review](../thesis/personal-agent-prior-art.md), [source register](../thesis/personal-agent-prior-art-sources.json), [bibliography](references.bib).
- [Architecture](architecture.md), [methods and ablations](methods.md), [costs and results](economics-and-results.md), [discussion and reproduction](discussion-and-reproduction.md).
- [Frozen pilot](../../experiments/codex-pilot-001/README.md), [analysis](../../results/codex-pilot-001/analysis/summary.json), [dialogue transcript](../../results/codex-pilot-001/dialogue-transcript.md).
- [Codex harness runbook](../research/personal-harness.md), [independent review](review.json), [build hashes](build-manifest.json).
- [SWE-bench replay records and reproduction](../../results/swe-replay-001/README.md), [independent audit](../research/swe-replay-audit.md).
- [New-host handover](../research/HANDOVER.md), [personal project setup](../research/project-usage-guide.md), [metered six-arm runner](../research/swe-bench-runner.md).

Rebuild with `bash scripts/build_paper.sh` from the repository root. It uses
Pandoc, XeLaTeX and Graphviz, which were exercised in this environment. Reproduce
the recorded analysis with
`python scripts/analyze_codex_pilot.py --output-dir results/new-analysis`.
The command creates a new output directory and does not call a model.

Author, institution and supervisor details remain for the author to complete.
Fastest Jira and Confluence were not reachable through available tools; the
repository's task register and import CSV preserve pending synchronization.
