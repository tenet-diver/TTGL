# Papers, reports and related work

Repository reading index, reviewed 15 November 2026. These are working papers
and local reports; this index makes no external publication or peer-review claim.
Read the [experiment catalog](EXPERIMENTS.md) for a consolidated status snapshot.
Older prose that says a study is running describes its dated checkpoint.

| Manuscript / report | Scope and recorded status | Reading and supporting material |
| --- | --- | --- |
| **Scaling to 100 concurrent agents** | Focused primary-source literature review of swarm organization, shared evidence, integration, communication and monitoring. Distinguishes shared-artifact work from verifier-selected alternative solutions; proposes a new controlled study without launching it. | [Review](research/agent-swarms-literature-review.md), [20-source register and repository checks](research/agent-swarms-sources.json) |
| **We have to combine — A conversation is all you need** | Conversational small-model/expert routing; live pilot, metered SWE-bench and historical replays. Large cost reductions often accompany quality loss; the overall target is unestablished. | [Paper index](paper/README.md), [Markdown](paper/paper.md), [HTML](paper/paper.html), [PDF](paper/paper.pdf), [Word](paper/paper.docx), [bibliography](paper/references.bib) |
| **Context and persistent-memory optimization** | Living development report: context transformations, chronological memory, LongMemEval-derived validation, caching and verification selection. Includes failed/rejected candidates. | [Index](paper/context-memory/README.md), [report](paper/context-memory/report.md), [progress register](research/context-memory-experiment-progress.md) |
| **Knowledge accumulation and generalization** | Memory-system review, completed coding diagnostics and proposed editable challenge graph. The draft predates some subsequent repository runs; use the separate first-wave report and continuation record for those outcomes. | [Index](paper/knowledge-accumulation/README.md), [paper](paper/knowledge-accumulation/paper.md), [repository results](research/repository-memory-wave-a-results.md), [continuation](research/knowledge-accumulation-study.md) |
| **Native Codex teams and shared knowledge** | Completed 24-cell, two-library development pilot; memory-aware 56-cell extension remains incomplete. Keep the separate interrupted 80-cell reservation distinct. | [Index](paper/codex-team-knowledge/README.md), [paper](paper/codex-team-knowledge/paper.md), [pilot](paper/codex-team-knowledge/pilot-results.md), [extension snapshot](paper/codex-team-knowledge/memory-aware-results.md), [appendix](paper/codex-team-knowledge/appendix.md), [reproduction](paper/codex-team-knowledge/REPRODUCING.md) |
| **Smallville memory: original, adaptations and measured results** | Original-style comparison, evidence-first adaptation, six-case validation and anonymous sensitivity audit; no default promoted. | [Final report](research/smallville-results.md), [source fidelity](research/smallville-source-fidelity.md), [online diagnostics](research/smallville-online-results.md) |
| **Luna memory and TokenEconomizer** | Memory-only and actual native-hook coding comparisons, maintenance overhead and a later Sol-maintained control. | [Results and methods](research/luna-memory-tokeneconomizer.md), [aggregate evidence](../tools/usage-monitor/studies/luna-memory-tokeneconomizer-final-results-001.json) |
| **Earlier broad thesis: We Gotta Combine!** | Supporting reviews of open-weight portfolios, agent communication, distillation, browser work and economics. Its original study hierarchy is superseded by later protocols. | [Chapter index](thesis/README.md), [personal-agent prior art](thesis/personal-agent-prior-art.md), [source register](thesis/personal-agent-prior-art-sources.json), [communication review](thesis/agent-communication.md) |

## Methods and bibliographies

- [Initial literature review](research/literature-review.md) and
  [research bibliography](research/references.bib).
- [Paper bibliography](paper/references.bib) and
  [additional references](paper/additional-references.bib).
- [Replication scope / ADR 0006](adr/0006-personal-agent-replication.md) and
  [benchmark/metering / ADR 0007](adr/0007-standard-benchmark-and-metered-handover.md).
- [Codex metering](research/codex-metering.md),
  [native runtime accounting](research/codex-runtime-metering.md), and
  [cache versus memory](research/cache-and-memory-reuse.md).
- [General-purpose routing constraints](research/router-generality.md),
  [routing rescue](research/routing-rescue-study.md),
  [verification feedback](research/verification-feedback-study.md), and
  [prospective learning methods](paper/learning-study.md).

The routing work is framed as replication and controlled extension of overlapping
prior work, including Router-R1 and EdgeWise. Classical distillation is prior art,
not the novelty claim. Model labels do not establish parameter counts, open weights
or local deployability. Persistent user memory is distinct from weight learning.

## Formats and reproduction

Current Markdown chapters, frozen protocols and result records take precedence
over older generated previews. The routing paper's PDF/Word files are older
working previews; their historical visual QA does not apply to later Markdown
changes. `bash scripts/build_paper.sh` rebuilds the routing manuscript only when
the reviewed Pandoc/XeLaTeX/Graphviz prerequisites are already available. Building
a preview is not new inference or an external publication.

Raw private logs, capture bodies, credentials and grader material are not bundled
with these documents. Public sanitized summaries and source hashes describe the
available evidence; unknown usage remains unknown. See [setup](../SETUP.md) and
the individual protocols before attempting reproduction.
