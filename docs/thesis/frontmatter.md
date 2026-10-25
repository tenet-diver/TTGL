---
title: "We Gotta Combine!"
subtitle: "Personal AI Through Open-Model Collaboration and Continual Distillation"
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

This document is a master's thesis manuscript in artificial intelligence, prepared before the proposed software-engineering and browser-task evaluations. Its research questions, background, system design, experimental protocol, analysis plan and limitations are written in advance. **The empirical results, result-dependent discussion and empirical conclusion are intentionally not written.** No claim that the proposed personal agent or model portfolio improves accuracy, reduces measured cost or benefits from adaptation is made. The central objective is an affordable, user-controlled personal agent that learns to work independently and to collaborate with external experts. Portfolio routing supplies an enabling mechanism; fixed two-model routing remains a restricted baseline and integration pilot.

A historical programming-problem replay and software-validation artifacts exist in the accompanying repository. They are development material for a different task distribution, and their measurements are not presented as evidence for this thesis's hypotheses. Each prospective domain study requires its own frozen model catalog, evaluation records and analysis. Published third-party benchmark accuracy and task-cost observations are background evidence. Illustrative token-cost calculations are explicitly labelled scenarios, not measured task prices or experiment results.

The source and pricing review has a cutoff of **25 October 2026**. A model catalog is a dated snapshot, not a promise that every listed model is deployable on the available hardware or that a floating API alias will remain unchanged. Secondary price observations require vendor confirmation before purchasing inference. The existing US$100 Runpod authorization funds a bounded feasibility pilot; it does not fund the entire proposed confirmatory matrix or additional closed-provider API spending.

Author, institution, degree wording, supervisor, institutional declarations and submission date are to be completed by the author. The manuscript does not invent those details or represent that an institution has approved the research.

# Abstract {.unnumbered}

An open model ecosystem can support personal AI in two complementary ways: by providing external expertise when a compact model cannot complete a task, and by supplying verified experience from which that personal model can learn. The resulting system need not treat the small model as merely a cheap substitute. It can maintain the user's goals, preferences and ongoing work, consult larger specialists, verify their proposals and integrate the results. Its usefulness depends on the quality of that cooperation as well as the capability retained for independent local use.

This thesis proposes a study of a small personal controller combined with a versioned portfolio of open-weight experts for agentic software engineering, with browser interaction as a transfer domain. The fixed-model cooperation study compares hierarchical assistance with local-only, large-model-only and flat-routing controls under shared personal context, tools and resource limits. A separate longitudinal study measures standalone student performance, collaboration quality and verified local completion across cumulative usage and distillation rounds. Distillation targets observable actions, expert requests, context selection, verified repairs and integration behavior. Router recalibration, personal memory and generator adaptation are separated experimentally.

The economic account includes dollars per assigned and successful task, teacher-data acquisition, verification, adaptation, model loading and state handoff. Local accessibility is assessed through measured memory, latency, offline functionality and artifact portability rather than assuming that a small checkpoint runs acceptably on every device. Reduced external-model use is a useful outcome only when task quality is maintained; improved cooperation may remain valuable when difficult tasks still require external expertise. New model releases and customer adapters enter through versioned development evaluations.

The intended contribution is a reproducible account of how the open ecosystem can strengthen a personal model over time, where compact-model capacity limits persist, and when cooperation produces benefits beyond giving a large model the same personal information. Democratization is the motivating objective; the proposed experiments measure technical access and capability proxies rather than claiming societal impact. The manuscript contains literature synthesis, architecture, experimental designs and attributable background evidence. It reports no TTGL outcomes for the proposed cooperative or longitudinal studies.

**Keywords:** personal AI; local agents; small language models; cooperative agents; model portfolios; verified distillation; continual adaptation; open-weight models.

# Acknowledgement {.unnumbered}

The project's guiding sentiment is: “Believe in me who believes in you.”
