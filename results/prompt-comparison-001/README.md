# Luna / Sol prompt combinations

![Cost versus task resolution](figures-002/combinations.png)

The original 12-task SWE-bench Verified panel and all three four-task development
studies are complete. They are separate experiments; the four development tasks
overlap the original panel and were already observed. Each development study ran
fresh, matched Luna-only and Sol-only controls with the same common solving
guidance as its assisted condition. Do not pool their counts or select the best
attempt for each task across studies.

| Study | Luna alone | Sol alone | Luna + expert access | Assisted cost reduction vs matched Sol | Expert calls |
|---|---:|---:|---:|---:|---:|
| Original, 12 tasks | 9/12 | 10/12 | 9/12 | 95.5% | 0 |
| Adaptive, 4 development tasks | 2/4 | 4/4 | 4/4 | 87.1% | 1 |
| Bounded cheap-first, same 4 tasks | 3/4 | 4/4 | 4/4 | 89.1% | 1 |
| Compact expert, same 4 tasks | 3/4 | 4/4 | 3/4 | 95.7% | 0 |

Costs include all measured controller, expert and integration model inference,
valued under the frozen published Codex Standard token-rate scenario. They are
not API invoices, subscription cash savings, or full deployment costs. The
shaded target in each graph is 95% relative Sol accuracy at 5% of Sol cost.
None of these assisted conditions meets both targets. Zero consultations in a
condition with access to an expert do not demonstrate collaboration. The compact
condition's zero expert calls also prevent attributing its outcome to expert
instruction compaction; acting-model sampling variation remains a confound.

The original pre-task router solved 11/12 for 31.1% lower scenario cost than Sol;
one-way help solved 9/12 for 92.1% lower cost, and fresh-expert help solved 8/12
for 92.4% lower cost. These point estimates on a small panel do not establish
population rankings. Native grading, not the models' reported test summaries,
determines success. Every completed study passed the independent event-counter,
patch-hash and native-report audit (108 assignments in total).

The development selection rule chose bounded cheap-first before any held-out
inference. The first reserved held-out control passed with a sentinel patch,
so model inference stopped. An audited pre-inference disposition now excludes
that invalid control without replacement under the original eligibility rule;
eleven reserved cases are undergoing readiness checks with the selected policy
unchanged. No held-out model inference has begun.
The same native report marks the expected fail-to-pass test as passing without
a repair; this case cannot demonstrate repair success under that evaluator.

The newer Pro V2 experiment is separately reserved in
`experiments/swe-pro-prompt-001`: 12 development tasks, then 24 disjoint validation
tasks. This is a subset study, not a full 642-task benchmark run. Neither its
controls nor its inference have run yet. Prompt tuning precedes open-weight,
distillation and RL experiments.

Reproduce the graph with `scripts/plot_prompt_combinations.py`; its provenance
file contains source record hashes and the exact points. Absolute dollars per
assigned task and resolution are shown in separate panels, with log cost axes.
The earlier horizontal rendering in `figures/` is retained as a layout preview;
`figures-002/` is the publication layout.
