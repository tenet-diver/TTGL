# Pre-results thesis

**Confidence-Aware Local–Remote Language Model Routing for Software Engineering**

Read the [PDF](thesis.pdf), edit the [Word document](thesis.docx), or open the [standalone HTML](thesis.html). The [assembled Markdown](thesis.md) is generated from the chapter files below. The manuscript contains no TTGL software-engineering results or result-dependent conclusions.

The study compares local-only, remote-only and routed agents under a common mini-SWE-agent harness. It specifies accuracy–cost frontiers, router calibration and allocation baselines, held-out evaluation, verified student distillation, and a bounded Runpod feasibility pilot. A separate no-tools LLM condition is a secondary interface comparison.

## Sources and scope

- [Introduction](introduction.md), [literature review](literature.md), [26-entry bibliography](references.bib), and [system design](system-design.md).
- [Current model and pricing review](model-landscape.md), [model catalog](model-catalog.csv), and [pinned evidence register](market-sources.json), reviewed 25 October 2026. Price observations are explicitly secondary and need provider confirmation before spending.
- [Published historical open/closed accuracy comparisons](accuracy-context.md) and [source records](accuracy-context-sources.json). These are background evidence, not the proposed experiment's results or a current-model ranking.
- [Experimental methodology](methodology.md), [analysis plan](analysis-plan.md), and [reproducibility, limitations and empty reporting templates](reproducibility-and-limits.md).
- [Evidence check](evidence-audit.json), [detailed checks](evidence-audit-details.json), [document validation](document-validation.json), and [artifact hashes](build-manifest.json).

The earlier LiveCodeBench replay remains in `docs/research/` and `results/`; its measurements do not populate this manuscript. Latest-model compatibility, the repository-level runner, model training and the confirmatory evaluation remain to be executed. The US$100 authorization covers one 80 GB Runpod GPU experiment and its associated Runpod costs; it is a feasibility allocation, not funding for the full study or additional API spending.

Author, institution and supervisor details must be completed by the author. Results, the result-dependent discussion and the empirical conclusion must be added only after the registered evaluation.

## Build

Install Python 3, Pandoc, Graphviz and XeLaTeX, including the `tocloft` package and DejaVu fonts. The manuscript was built with Pandoc 3.1.11.1. From the repository root:

```bash
bash scripts/build_thesis.sh
```

The script rebuilds the architecture illustration, assembled Markdown, A4 PDF, DOCX, self-contained HTML with MathML, and the artifact hash manifest. Edit the individual chapters rather than the generated `thesis.md`. Document timestamps and generator metadata can change binary hashes between otherwise equivalent builds. This command does not call a model or provision GPU resources.
