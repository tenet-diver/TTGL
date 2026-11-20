# Historical experiment memory for Codex harness optimization

## 1. Abstract

We test whether structured records of earlier experiments improve an
optimizer's ability to adjust instructions for a fixed coding model.
The Observatory pilot compares four historical-memory projections from the
same starting harness with equal round and candidate budgets. Optimization
and final assessment use disjoint Python repair tasks and deterministic
independent checks. We measure held-out repair success and the resource cost
of optimization. Native usage is retained through Observatory. The four arms
finished at 3/4, 2/4, 4/4 and 2/4. Three arms used identical final settings,
so this one-block pilot does not establish a memory benefit.

## 2. Research questions

We ask whether successful history improves generalization (H1, C1 minus C0),
whether outcomes of unsuccessful experiments are additionally useful (H2,
C2 minus C1), and whether predictions, diagnostic hypotheses and rationale add
value over outcomes alone (H3, C3 minus C2). C3 minus C0 describes the full
historical-memory effect. For H4 we compare improvements per unit of measured
optimization tokens, elapsed wall time and the stated inference-rate scenario.

Verified coding repairs are the experimental proxy for the effectiveness of
technical problem-solving. The experiment does not measure commercial or
scientific innovation directly.

## 3. Related work

Yu et al.'s [Self-Improvement Memory Enables Continual Recursive Self-Improvement](https://arxiv.org/html/2611.18856v1)
places memory with the harness proposer and selector. It records problem
diagnoses, attempted modifications, predicted repairs, measured outcomes,
and provenance. The paper uses matched target continuations across new
benchmarks or policy models and updates memory during the target run. In the
paired Terminal-Bench 2.1 to 4 coding comparison, the authors report a mean
2.36 percentage-point advantage for SIM, 95% CI 1.05–3.68, across ten
independently evolved source harnesses. Their signed-rank check agrees with
the paired result. The study also reports a negative pair and nonuniform
results in a separate cross-generation transfer series. See Sections 3–4
and Appendices B–F for outcome definitions, models, allocations, memory
matching and case histories.

The current project reuses the [Observatory live harness trial](../../../tools/usage-monitor/studies/live-harness-results-001.md)
and [progress-replay evidence](../../../tools/usage-monitor/studies/progress-replay-results-002.md).
They establish that the source outcomes in the historical bank were actually
observed, including a failed registered acceptance gate and a later revision.

## 4. Methodology

We reproduce the central matched-start mechanism. Historical experience is
supplied to the optimizer while policy weights, starting prompt harness,
optimization task feedback, budgets and evaluation stay fixed. The final
harness is selected entirely on development tasks. The four projections
isolate outcomes and causal explanations more directly than the paper's
cold-start, harness-only, problem-only and full-SIM conditions. C0 receives
no record from the historical bank. Current-run observations use the same
schema in all four conditions.

We adapt the paper substantially for a small, reproducible pilot. We use a
fixed preexisting bank and a hand-defined common seed. The paper evolves the
source harness separately for each independent pair and carries it into target
optimization. Our bank is frozen across target runs. The original method
updates an explicit SIM memory during the target run. We retain target
observations separately and identically across arms to isolate prior
information. Our selector is deterministic and receives only grades and
usage. The paper's learned selector also receives SIM and can consider
qualitative factors. Our interventions are bounded instruction changes.
The paper also permits edits to harness code, tools and runtime logic.

## 5. Implementation

The runner reuses Observatory's ChatGPT-bound native Codex execution,
per-thread usage reconciliation, immutable artifact naming and loopback local
S3/PG retention. Fresh Git worktrees contain only public task files. Actor
tools run under Bubblewrap with no network or access to local Codex credentials.
The independent grader runs elsewhere and compares a candidate's outputs to
host-held expectations. A native call has durable registration, admission and
terminal receipts. A missing terminal receipt after admission stops resume at
that slot. The historical bank contains explicit source trial IDs and hashes.
Run instructions and the publication path are in the [README](README.md).

## 6. Experimental setup

`gpt-6-luna` at low reasoning effort is both optimizer and policy, using native
Codex CLI 0.170.0 and the authorized local ChatGPT subscription. The benchmark
is Observatory Python Repair 001. All 11 reference controls passed independent
checks and all 11 unchanged starter candidates failed them. All public tests
passed on the starters, so public success alone cannot satisfy the independent
criterion. The optimization pilot uses three tasks and the final comparison
uses four fresh tasks. Historical measurements come from separate registered
studies, with the historical fixtures in the new benchmark reserved for a
future prospective study.

There is one registered block of four arms, with five rounds and at most one
candidate per round. Condition order is randomized using the registered seed.
All final attempts use one rollout per task. The paper used Gemini 3.8 Flash
in its main coding comparison, ten rounds, five candidates and five rollouts
per task on much larger Terminal-Bench splits. We report this study as an
Observatory adaptation and pilot.

## 7. Results

The initial live smoke completed a new out-of-suite code edit with three
independent checks passing. It recorded 65,013 native tokens and about
21.6 invocation seconds. Its API-equivalent estimate was $0.00352. The smoke
validates transport, actor isolation and evidence retention and is excluded
from the pilot scores and pilot costs.

All four arms completed five optimization rounds. The common starting
harness passed 3/4 held-out tasks in separate baseline attempts. The table
excludes those shared baseline evaluations from arm-level resource costs.

| Arm | Runs | Held-out passes | Optimization tokens | Held-out tokens | API-equivalent USD | Optimization wall seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C0 | 1 | 3/4 | 1,148,757 | 190,269 | 0.04667 | 287.9 |
| C1 | 1 | 2/4 | 970,251 | 179,453 | 0.03670 | 251.6 |
| C2 | 1 | 4/4 | 1,127,937 | 350,063 | 0.04416 | 264.4 |
| C3 | 1 | 2/4 | 1,211,080 | 180,007 | 0.04883 | 334.3 |

The pilot finished 100 native invocations using 5,859,729 tokens and
$0.19191 at the pinned API-equivalent rates. Optimization accounted for
4,613,007 tokens and held-out evaluation used 1,246,722. Wall clock was
23 minutes 50 seconds. Sum of native invocation envelopes was 41 minutes
13 seconds because task calls overlapped. The ledger reconciles all native
receipts, and independent grade replay matched all 80 coding submissions.
The preflight smoke added 65,013 tokens separately. No new model calls
were used to generate the historical bank. Original trial costs remain in
the bank, and implementation and supervision are outside the pilot total.

The retained harness scored 3/3 at every optimization round in every
condition. The round record contains 19 evaluated candidates, one accepted change and
one no-op proposal. C3's accepted
verification checklist retained 3/3 development passes at 135,158 tokens
versus the common incumbent's 154,982, a 12.8% reduction for that comparison.
It then passed 2/4 held-out tasks. C0, C1 and C2 all retained the same seed.
Their distinct scores therefore include execution variation under identical
harness settings.

At round one, projected history used 0, 894, 1,349 and 2,739 UTF-8 bytes.
Measured first-request input was 9,302, 9,507, 9,604 and 9,856 tokens,
respectively. These first-request counts include shared native context.
Relative to C0 the increments were 205, 302 and 554 input tokens.

[Machine-readable measurements](../../../results/sim-memory-ablation/pilot-001/summary.json) ·
[Rounds](../../../results/sim-memory-ablation/pilot-001/rounds.csv) ·
[Performance chart](../../../results/sim-memory-ablation/pilot-001/performance.svg) ·
[Resource chart](../../../results/sim-memory-ablation/pilot-001/resources.svg)

## 8. Statistical analysis

Each independent repetition is one paired observation. Individual held-out
repairs are not independent optimization runs. For repeated blocks, the
analysis reports paired mean differences and standard deviations, standardized
paired effects where defined, paired bootstrap intervals over repetitions and
an exact two-sided sign-flip test. All contrasts are prespecified. A single
block yields observed differences with no replicate-level confidence interval
or p-value. The observed differences were C1–C0 −25, C2–C1 +50, C3–C2 −50 and
C3–C0 −25 percentage points. Their single matched block cannot estimate
across-run variance. The most favorable raw contrast, C2–C1, compares
identical final harness settings. The pilot gives no reliable support for
H1–H4. Relative to the separate common baseline, gain per million
optimization tokens was 0.00, −25.77, +22.16 and −20.64 percentage points.
The apparent efficiency differences inherit the same rollout variability.

## 9. Discussion

Historical outcome records may help the optimizer reconsider plausible but
unverified workflow changes. They may also favor earlier advice whose
execution boundaries differ from the current task. The case analysis looks
for cited observations in proposal receipts and follows the independent
evaluation and selection decision for each intended reuse. Citations
establish that memory was referenced, without isolating its causal effect on
any individual choice. In C3 round four the proposer cited the failed
progress-replay gate and preferred scoped reads with an explicit way to
expand incomplete output. The candidate showed no material improvement.
C1 round one proposed grouped tool use and lost an incumbent passing task.
The proposer later observed that historical reversible compression is a
different intervention from requesting grouped commands. These examples
illustrate useful qualifications and the risk of transferring a seemingly
similar tweak. They do not establish the benefit or harm of any record.

## 10. Threats to validity

The historical archive is small, reused and focused on evidence presentation.
Some source diagnostics used deliberately constructed log inputs. Root causes
are attributed hypotheses. The candidate space uses predefined settings and
may omit the interventions that benefited the original study. Prompt length
varies with the information available. We record native inputs and historical
projection byte lengths, and do not treat repeated input as new knowledge.
The tiny held-out denominator has 25 percentage points of granularity in one
block. Provider behavior can vary within the recorded model version. Fresh
sessions and common budgets reduce exposure to unrelated agent history.

## 11. Conclusions

The pilot verifies that Observatory can measure the four treatments end
to end. It found no supported generalization benefit from this fixed bank
and tiny prompt-harness search. Estimating an effect near the paper's requires a larger held-out
suite and independent paired source histories. In a closer replication,
evolve each source harness once, then initialize the corresponding C0 and C3
target arms from that exact source snapshot and extend the benchmark across
a source-to-target transition. Retain C1 and C2 as separately registered
mechanism ablations.

## 12. Reproducibility instructions

See the [runbook](README.md) for qualified CLI entry points, the frozen
protocol and bank, raw retention rules and the output formats. Exact source
and provider versions are recorded with each invocation. Measured estimates
are API-equivalent inference scenarios. Provider quota consumption and
subscription cash are unknown.

The completed aggregate was retained and read back byte for byte from
local SILO. Observatory's evaluation endpoint returned the single scoped
record. An initial publication encoded its two index rows as JSON strings.
The publisher and those two derived rows were corrected against the same
verified aggregate, and the original archived bytes and native evidence
were preserved.
