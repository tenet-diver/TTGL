---
title: "Confidence-Aware Local–Remote Language Model Routing for Software Engineering"
subtitle: "A cost–accuracy study with verified teacher distillation"
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

This document is a master's thesis manuscript in artificial intelligence, prepared before the proposed repository-level software-engineering evaluation. Its research questions, background, system design, experimental protocol, analysis plan and limitations are written in advance. **The empirical results, result-dependent discussion and empirical conclusion are intentionally not written.** No claim that the proposed dual-model system improves accuracy, reduces measured cost or benefits from distillation is made.

A historical programming-problem replay and software-validation artifacts exist in the accompanying repository. They are development material for a different task distribution, and their measurements are not presented as evidence for this thesis's software-engineering hypotheses. The prospective repository-level study requires its own frozen model catalog, evaluation records and analysis. Published third-party benchmark claims, where included in the model-landscape chapter, are clearly distinguished from the proposed study's unobserved results.

The source and pricing review has a cutoff of **25 October 2026**. A model catalog is a dated snapshot, not a promise that every listed model is deployable on the available hardware or that a floating API alias will remain unchanged. Secondary price observations require vendor confirmation before purchasing inference. The existing US$100 Runpod authorization funds a bounded feasibility pilot; it does not fund the entire proposed confirmatory matrix or additional closed-provider API spending.

Author, institution, degree wording, supervisor, institutional declarations and submission date are to be completed by the author. The manuscript does not invent those details or represent that an institution has approved the research.

# Abstract {.unnumbered}

Large language models increasingly support software-engineering work through tools that inspect repositories, edit code and execute tests. High-capability models can be expensive to operate, while smaller models can run on user-owned hardware but may fail on tasks requiring substantial repository understanding or multi-step repair. A dual-model system seeks to reconcile these constraints by assigning suitable work to a local model and delegating selected work to a stronger remote model. Its value depends not merely on reducing remote calls, but on retaining useful software-engineering accuracy after accounting for routing, verification, failed attempts and local computation.

This thesis proposes a controlled evaluation of confidence-aware local–remote routing for repository-level issue resolution. The design compares a dual-model system with local-only and remote-only agents using the same tool harness, task environments and stopping rules. Random and rule-based routing, matched on estimated cost using calibration data, establish allocation baselines; a separate no-tools language-model condition examines the contribution of the surrounding agent system without conflating it with routing. The router estimates the expected quality improvement and incremental cost of delegation, with calibration and action thresholds selected on development data. A secondary study investigates whether verified teacher-output distillation improves the local model and changes the achievable quality–cost frontier.

The proposed evaluation uses pinned software-engineering benchmarks, paired task outcomes, held-out calibration, repository-level generalization checks and uncertainty estimates that respect task dependence. Financial accounting distinguishes paid API tokens from local hardware and self-hosted GPU costs. Current open-weight and closed-model candidates are assessed through a dated evidence catalog; published performance claims with different harnesses are not treated as controlled comparisons. The intended contribution is a reproducible account of when dual-model delegation is worthwhile, how reliably its confidence estimates support decisions, and which costs or failure modes limit its practical use. The manuscript reports no empirical outcomes for these questions.

**Keywords:** software-engineering agents; model routing; selective prediction; calibrated confidence; cost-sensitive learning; knowledge distillation; open-weight language models.

# Acknowledgement {.unnumbered}

The project's guiding sentiment is: “Believe in me who believes in you.”
