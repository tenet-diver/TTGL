# We have to combine — A conversation is all you need

**Using small language models as conversational routers for agentic software engineering.**

Read the [PDF](paper.pdf), edit the [Word document](paper.docx), or open the
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
protocol, economic accounting, live pilot results, limitations and next-study
design. The proposed confirmatory gate uses a three-point quality margin and a
25% practical savings target; neither is established by the pilot.

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
noninferiority claim is supported**, and token/dollar costs remain unknown.

- [Prior-art review](../thesis/personal-agent-prior-art.md), [source register](../thesis/personal-agent-prior-art-sources.json), [bibliography](references.bib).
- [Architecture](architecture.md), [methods and ablations](methods.md), [costs and results](economics-and-results.md), [discussion and reproduction](discussion-and-reproduction.md).
- [Frozen pilot](../../experiments/codex-pilot-001/README.md), [analysis](../../results/codex-pilot-001/analysis/summary.json), [dialogue transcript](../../results/codex-pilot-001/dialogue-transcript.md).
- [Codex harness runbook](../research/personal-harness.md), [independent review](review.json), [build hashes](build-manifest.json).

Rebuild with `bash scripts/build_paper.sh` from the repository root. It uses
Pandoc, XeLaTeX and Graphviz, which were exercised in this environment. Reproduce
the recorded analysis with
`python scripts/analyze_codex_pilot.py --output-dir results/new-analysis`.
The command creates a new output directory and does not call a model.

Author, institution and supervisor details remain for the author to complete.
Fastest Jira and Confluence were not reachable through available tools; the
repository's task register and import CSV preserve pending synchronization.
