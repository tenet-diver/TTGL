# We Gotta Combine!

**Cost-Aware Routing of Open-Weight Specialist Models Across Software Engineering and Browser Tasks**

Read the [PDF](thesis.pdf), edit the [Word document](thesis.docx), or open the [standalone HTML](thesis.html). The [assembled Markdown](thesis.md) is generated from the chapter files. This is a pre-results master's thesis: the proposed TTGL portfolio, browser and customer-adaptation experiments have no performance results yet.

The assistant selects among multiple eligible specialist configurations according to expected success, total task cost, latency and customer constraints. Small models may run locally or remotely. Task-level selection is the default; phase and per-call switching are separate experiments. Customer adaptation uses compatible base-specific artifacts, not an assumed universally portable LoRA. The original two-model design is retained as a restricted baseline and integration pilot.

## Chapters and evidence

- [Introduction](introduction.md), [foundations](literature.md), [46-entry bibliography](references.bib), and [portfolio system design](system-design.md).
- [Current model and pricing review](model-landscape.md), [model catalog](model-catalog.csv), and [pinned market evidence](market-sources.json), reviewed 25 October 2026. Direct-provider price observations are explicitly secondary and need confirmation before spending.
- [Published historical accuracy](accuracy-context.md) and [source records](accuracy-context-sources.json).
- [Task-level economics](task-economics.md), [historical dollars per task/success](task-price-comparisons.csv), [illustrative current-rate scenarios](task-price-scenarios.csv), [economic sources](task-economics-sources.json), and [arithmetic/source checks](task-price-checks.json). Historical records, hypothetical scenarios and future measured costs are separate evidence classes.
- [Browser, frontend and language evaluation](browser-domain.md) and [browser source register](browser-sources.json).
- [Customer adaptation, deployment and switching](adaptation-and-switching.md) and [source register](adaptation-sources.json).
- [Controlling ensemble protocol](ensemble-methodology.md), [routing research sources](ensemble-methods-sources.json), [detailed SWE procedures and restricted-pair pilot](methodology.md), and [analysis plan](analysis-plan.md).
- [Reproducibility, limitations and empty reporting templates](reproducibility-and-limits.md), [original evidence check](evidence-audit.json), [detailed checks](evidence-audit-details.json), [portfolio review](portfolio-review.json), [document validation](document-validation.json), and [artifact hashes](build-manifest.json).
- [Architecture decision](../adr/0004-specialist-model-portfolio.md) and [local work-item state](../research/task-state.json).

The primary confirmatory comparison is a frozen open-weight portfolio against a strong fixed configuration selected on development data, under one software-engineering harness. Browser tasks are a separate replication; frontend rendering, functional frontend behavior and browser navigation have distinct outcomes. Published cross-harness claims cannot establish the combined model frontier. New releases enter versioned development evaluations before router recalibration; final-test results cannot select the next winner.

The earlier LiveCodeBench replay remains in `docs/research/` and `results/`; its measurements do not populate this manuscript. Latest-model integration, the expanded agent runner and empirical execution remain pending. The US$100 authorization covers one 80 GB Runpod GPU experiment and associated Runpod costs; it does not fund the full cross-domain matrix or additional API spending. Author, institution and supervisor details remain for the author to complete. Results and result-dependent conclusions will be written after evaluation.

## Rebuild

Install Python 3, Pandoc, Graphviz and XeLaTeX, including `tocloft`, `etoolbox` and DejaVu fonts. The manuscript was built with Pandoc 3.1.11.1. From the repository root:

```bash
python scripts/build_task_price_table.py --verify-upstream
bash scripts/build_thesis.sh
```

The first command checks the pinned public leaderboard and regenerates task-cost CSVs; it makes no model calls. Omit `--verify-upstream` for offline arithmetic regeneration, which records that fresh upstream verification was not requested. The second command builds the architecture illustration, assembled Markdown, A4 PDF, DOCX, self-contained HTML with MathML and artifact hashes. Edit individual chapters rather than generated `thesis.md`. Timestamps and generator metadata can change binary hashes between otherwise equivalent builds. Neither command provisions GPU resources.
