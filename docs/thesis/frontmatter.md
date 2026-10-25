---
title: "We Gotta Combine!"
subtitle: "Cost-Aware Routing of Open-Weight Specialist Models Across Software Engineering and Browser Tasks"
author: "Author name and university affiliation to be completed"
date: "25 October 2026 — pre-results manuscript"
lang: en-GB
bibliography: references.bib
link-citations: true
reference-section-title: References
documentclass: report
classoption: [11pt, oneside]
geometry: margin=25mm
papersize: a4
mainfont: DejaVu Serif
sansfont: DejaVu Sans
monofont: DejaVu Sans Mono
colorlinks: true
toc-depth: 2
numbersections: true
---

# Manuscript status {.unnumbered}

This document is a master's thesis manuscript in artificial intelligence, prepared before the proposed software-engineering and browser-task evaluations. Its research questions, background, system design, experimental protocol, analysis plan and limitations are written in advance. **The empirical results, result-dependent discussion and empirical conclusion are intentionally not written.** No claim that the proposed model portfolio improves accuracy, reduces measured cost or benefits from adaptation is made. The revised scope replaces a fixed local/remote pair with a pool of eligible specialist models; the earlier two-model protocol remains a restricted baseline and integration pilot.

A historical programming-problem replay and software-validation artifacts exist in the accompanying repository. They are development material for a different task distribution, and their measurements are not presented as evidence for this thesis's hypotheses. Each prospective domain study requires its own frozen model catalog, evaluation records and analysis. Published third-party benchmark accuracy and task-cost observations are background evidence. Illustrative token-cost calculations are explicitly labelled scenarios, not measured task prices or experiment results.

The source and pricing review has a cutoff of **25 October 2026**. A model catalog is a dated snapshot, not a promise that every listed model is deployable on the available hardware or that a floating API alias will remain unchanged. Secondary price observations require vendor confirmation before purchasing inference. The existing US$100 Runpod authorization funds a bounded feasibility pilot; it does not fund the entire proposed confirmatory matrix or additional closed-provider API spending.

Author, institution, degree wording, supervisor, institutional declarations and submission date are to be completed by the author. The manuscript does not invent those details or represent that an institution has approved the research.

# Abstract {.unnumbered}

Language models differ in their strengths, deployment requirements and cost. A model suited to backend repair need not be the best choice for frontend development or browser interaction; parameter count and a single aggregate benchmark do not establish a universal ordering. An assistant can instead select from a portfolio of open-weight specialists, with optional closed-model references, according to expected task performance, total cost, latency and customer constraints. Small models may run locally or remotely, and customer-specific adaptation may improve selected members of the portfolio.

This thesis proposes a controlled evaluation of cost-aware portfolio routing across software-engineering and browser tasks. The primary software-engineering comparison tests a frozen multi-model policy against a strong fixed model selected on development data under a common agent harness. Domain-specific selection, two-model routing, random allocation and simple rules provide additional controls; browser interaction supplies a separate transfer study. Accuracy–cost frontiers are reported in dollars per assigned task and per successful task, with workload-specific success definitions and complete accounting for failures. Task-level model selection is the default. Phase-level and per-call switching are evaluated separately, including model loading, context reprocessing and state-transfer costs.

The design separates portfolio selection, router recalibration and model adaptation. New releases are admitted through versioned development evaluations, while final tests remain unavailable for selection. Customer adapters are associated with compatible base-model revisions; shared training data does not imply interchangeable adapter weights or key–value caches. The study measures whether additional specialists or adaptation improve the attainable frontier enough to justify their operational cost. Published model and price evidence informs candidate selection but does not establish a universal best combination. The intended contribution is a reproducible account of how closely a deployable policy can approach the capabilities of its eligible model pool at a chosen price sensitivity. No empirical outcomes for that hypothesis are reported.

**Keywords:** model portfolios; software-engineering agents; browser agents; cost-sensitive routing; calibrated confidence; customer adaptation; LoRA; open-weight language models.

# Acknowledgement {.unnumbered}

The project's guiding sentiment is: “Believe in me who believes in you.”
