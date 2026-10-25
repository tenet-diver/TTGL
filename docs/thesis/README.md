# We Gotta Combine!

**Personal AI Through Open-Model Collaboration and Continual Distillation**

Read the [PDF](thesis.pdf), edit the [Word document](thesis.docx), or open the [standalone HTML](thesis.html). The [assembled Markdown](thesis.md) is generated from the chapter files. This is a pre-results master's thesis: the proposed cooperative and longitudinal studies have no TTGL performance results yet.

The central objective is to democratize useful AI through an affordable personal model that works locally, collaborates with open-model experts and learns from verified experience. Its role includes personal memory, task interpretation, context selection, expert requests, verification and integration. Independent local capability and better cooperation are separate outcomes; reducing expert calls is useful only when quality is retained. Routing supplies one component of this architecture.

## Core chapters

- [Introduction and research questions](introduction.md), [foundations](literature.md), and [54-entry bibliography](references.bib).
- [Evidence for agent learning](agent-learning-evidence.md) and [primary-source register](agent-learning-sources.json), including published improvements, regressions and plateaus.
- [Personal-agent system design](system-design.md), [cooperative controller and controlled experiment](personal-controller.md), and [controller/memory sources](controller-sources.json).
- [Learning through usage and distillation](longitudinal-learning.md), with a [machine-readable prospective plan](longitudinal-plan.json). Rounds track cumulative arrivals, verification yield, target tokens and compute; final tests remain sealed during learning.
- [Analysis and study hierarchy](analysis-plan.md), [reproducibility and empty reporting templates](reproducibility-and-limits.md), [source/design audit](personal-review.json), [document validation](document-validation.json), and [artifact hashes](build-manifest.json).

Study 1 is the current primary cooperation experiment: a study-unadapted small controller plus one strong expert versus that same strong model acting directly, with equal personal context, tools and resource caps. Accepted task success includes benchmark resolution and feasible mandatory user constraints. Study 0 supplies flat-routing controls. Study 2 is a separate proposed longitudinal experiment, distinguishing standalone learning, allocation changes and learned collaboration. Their hypotheses cannot substitute for one another after seeing results.

## Supporting studies and economic evidence

- [Model and price landscape](model-landscape.md), [model catalog](model-catalog.csv), and [market sources](market-sources.json), reviewed 25 October 2026. Direct-provider price observations are secondary where vendor confirmation was unavailable.
- [Historical benchmark accuracy](accuracy-context.md) and [source records](accuracy-context-sources.json).
- [Task-level economics](task-economics.md), [historical dollars per task/success](task-price-comparisons.csv), [illustrative token-price scenarios](task-price-scenarios.csv), [economic sources](task-economics-sources.json), and [arithmetic/source checks](task-price-checks.json).
- [Browser, frontend and language evaluation](browser-domain.md), [browser sources](browser-sources.json), [adaptation and switching](adaptation-and-switching.md), and [adaptation sources](adaptation-sources.json).
- [Enabling portfolio protocol](ensemble-methodology.md), [routing sources](ensemble-methods-sources.json), [detailed repository procedures](methodology.md), and [prior portfolio review](portfolio-review.json).
- [Personal-agent ADR](../adr/0005-personal-agent-and-learning.md), [portfolio ADR](../adr/0004-specialist-model-portfolio.md), and [local work-item state](../research/task-state.json).

Historical figures and hypothetical prices do not populate the unrun studies' result tables. The earlier LiveCodeBench replay remains separately documented in `docs/research/` and `results/`. Latest-model integration, the cooperative runner, repeated training and device measurements remain pending. The US$100 authorization covers one 80 GB Runpod GPU feasibility experiment and associated Runpod costs; it does not fund the full program or additional API spending. Author, institution and supervisor details remain for the author. Results and result-dependent conclusions will be written after evaluation.

## Rebuild

Install Python 3, Pandoc, Graphviz and XeLaTeX, including `tocloft`, `etoolbox` and DejaVu fonts. The manuscript was built with Pandoc 3.1.11.1. From the repository root:

```bash
python scripts/build_task_price_table.py --verify-upstream
bash scripts/build_thesis.sh
```

The first command checks a pinned public leaderboard and regenerates task-cost CSVs; it makes no model calls. Omit `--verify-upstream` for offline arithmetic regeneration, which records that fresh upstream verification was not requested. The second builds the architecture illustration, assembled Markdown, A4 PDF, DOCX, standalone HTML with MathML and artifact hashes. Edit individual chapters rather than generated `thesis.md`. Timestamps can change binary hashes between otherwise equivalent builds. Neither command provisions GPU resources.
