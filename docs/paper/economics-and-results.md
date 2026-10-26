# Measurement and economic analysis

## What counts as saving money

The main hypothesis concerns the whole system, not merely the number of calls
to a strong model. For assigned task $i$, define

$$C_i=C_{S,i}+C_{L,i}+C_{\mathrm{router},i}+C_{\mathrm{tools},i}
       +C_{\mathrm{handoff},i}+C_{\mathrm{retry},i}.$$

For API services, each component uses observed billable input, cached input,
output and separately billed reasoning/tool categories at a dated endpoint price.
For rented inference, include occupied instance time, startup, model loading,
storage and cleanup. Local hardware has both a marginal-cost scenario and a
fully allocated scenario including energy and amortization. Training and
experience-acquisition costs are separately amortized over a stated task horizon.
Do not add a token-price estimate to an instance bill when they represent the
same inference expense.

Cost per assigned task is $\sum_i C_i/N$. Cost per resolved task is
$\sum_i C_i/\sum_i Y_i$, so failed attempts remain in the numerator. If there are
no successes, the latter ratio is undefined, not zero. The proposed cost ratio
is $\bar C_C/\bar C_L$ after the quality gate. Savings are $1-\bar C_C/\bar C_L$.
Unknown cost components prevent a full-cost claim. Counting only paid cloud
tokens supports a narrower API-bill claim, which must be labelled accordingly.

Conversation can save expensive model work but add repeated context, latency
and cache misses. A resumed conversation preserves logical state, not a
guaranteed physical KV cache. Switching models or adapters can require prompt
reprocessing. Record actual cache usage where the provider exposes it, and
measure cold versus warm service conditions in open-model deployment. LoRA
adapters are tied to compatible base models; arbitrary cross-model adapter
sharing is not assumed.

Report an empirical quality–cost frontier at development-selected operating
points. Changing the price sensitivity, maximum expert turns or escalation
threshold creates different policies. The final test cannot choose the best
threshold retrospectively. Decision quality includes false local confidence,
unnecessary consultations, unresolved requests, useful expert replies rejected
and harmful replies accepted. A correlation between expert calls and failure is
not causal evidence that experts hurt: difficult tasks may trigger those calls.

## Published price and accuracy context

The supporting source audit contains an independently reconciled historical
SWE-bench Verified comparison using mini-SWE-agent 2.0.0, 500 assigned issues per
submission, dated 17 February 2026 [@ttglhistoricalleaderboard2026]. These are third-party reported inference
costs, not invoices, full infrastructure expenses or current-model prices.
They must not be mixed with this four-task pilot to rank the architectures.

| Historical model | Resolution | Reported USD / assigned task | Derived USD / resolved task |
|---|---:|---:|---:|
| MiniMax M2.5 high, open weights | 75.8% | 0.0733 | 0.0967 |
| Claude Opus 4.6, closed | 75.6% | 0.5515 | 0.7295 |
| GLM 5 high, open weights | 72.8% | 0.5344 | 0.7341 |
| GPT-5.2 high, closed | 72.8% | 0.4736 | 0.6505 |
| Claude Sonnet 4.5 high, closed | 71.4% | 0.6579 | 0.9214 |
| Kimi K2.5 high, open weights | 70.8% | 0.1466 | 0.2070 |

The exact source revision, 3,000 per-instance cost records and arithmetic are
registered in the supporting `task-economics-sources.json`,
`task-price-checks.json` and `task-price-comparisons.csv`. The price per resolved
task includes spending on unsuccessful assignments. Matching a named scaffold
and benchmark improves comparability but does not erase differences in model
settings, serving or submission procedures. These historical figures establish
that open-weight and closed systems can occupy different cost–quality points;
they do not identify the present best model.

The 25 October 2026 model catalog separately records recent Qwen, DeepSeek, GLM,
Kimi and closed-provider releases, licenses and price-source limitations. For
example, a current compact Qwen checkpoint is a candidate for an eventual
open-model controller replication, whereas very large sparse DeepSeek models
do not become deployable on one 80-GB GPU merely because their active parameter
count is small. Current inference frameworks and model compatibility require a
real preflight. Model selection is frozen per experiment, rather than silently
substituting the newest release mid-run.

# Live engineering-pilot results

## Execution and independent grading

The pilot completed **16 assigned model runs**: four conditions on four bugs from
two repositories. Three bugs are from tqdm and one from PySnooper; some concern
related Boolean/initialization behavior. These are four assignments, not four
independent repository clusters. All eight pre-model evaluator controls passed:
each buggy version failed and each official fixed version passed its selected
regression module. A later integrity check confirmed the recorded source and
test hashes before grading the submissions.

All workers used fresh conversations, explicitly requested medium reasoning
effort and the same pinned Python test environment. The primary matrix used
Luna and Sol through Codex's collaboration interface. No Runpod GPU was created.
No model was trained. The frozen protocol hash is recorded in every grading
report, and the individual submissions, test output, JUnit records and analysis
inputs are archived. Reported model self-checks are not substituted for the
independent grading below.

| Condition | Functional regression success | Accepted under frozen artifact rule | Expert consultations |
|---|---:|---:|---:|
| Single Luna | 3/4 | 3/4 | 0 |
| Single Sol | 4/4 | 4/4 | Not applicable: Sol is the sole worker |
| Task-only prompt router | 4/4 | 2/4 | Router selected Luna for every task |
| Optional conversational Luna controller | 3/4 | 0/4 | 0 |

The two columns answer different questions. The frozen grader rejects **any
change to an existing test file**, including adding assertions, while allowing
new test files. All four conversational workers and two routed workers edited
an original test file. Those submissions therefore fail the artifact policy
even where the independent regression tests pass. The policy is stricter than
the ordinary meaning of “do not weaken tests,” and the personal-worker prompt
said “preserve existing tests; adding tests allowed.” This wording leaves room
for additive changes. The resulting acceptance difference is a protocol and
instruction-adherence issue, not evidence that all those patches are incorrect.
The rule was not changed after outcomes, and both endpoints are preserved.

There were two functional failures in the matrix. The Luna-only PySnooper patch
applied representation again to a custom formatter's returned string, adding
unwanted quotes; the independent custom-representation tests caught it. The
optional-conversation tqdm Boolean patch returned false when neither iterable
nor total was supplied, while the registered regression requires a TypeError.
Its added local test instead endorsed the altered behavior. These cases show
why an agent's passing self-tests cannot replace independent acceptance tests.

Every task-only routing decision selected Luna. Its 4/4 functional score versus
the separate Luna-only 3/4 run is not evidence that the router identified a
better backend: it chose the same backend on every issue. These are different
stochastic sessions with slightly different role instructions. Likewise, the
optional conversational controllers all chose zero consultations, so their
outcomes do not estimate the value of an actual dialogue. No held-out labels
were used to revise or rerun those submissions.

## Forced bidirectional mechanism check

Because no optional controller exercised the expert channel, a separate
engineering check required a two-turn expert exchange on the original PySnooper
base. This was planned after observing the lack of consultations and is not a
fifth performance condition or an independent held-out issue.

Luna inspected the code and sent selected context to a fresh Sol expert. The
expert was instructed to ask one clarification question before proposing a
solution. It asked whether custom representation should apply to watched and
expanded values or only ordinary frame locals. Luna investigated the rendering
paths, answered that the task concerned ordinary locals and asked the same
expert thread for a proposal. Sol supplied a design preserving the existing
representation-shortening and error-handling path. Luna implemented and tested
the patch. The independent selected module passed **30/30 tests**, with no
artifact-policy violation. The visible dialogue is archived verbatim as reported
by the controller.

The first collector invocation used a relative JUnit output path; pytest passed
but the collector looked in the wrong directory and recorded zero tests. The
original record is retained. Regrading the unchanged patch with an absolute
output path recovered the 30 passing checks. This was an evaluator-output-path
correction, not another model attempt. The two reports have the same patch hash.

This establishes that live clarification, reply, proposal and integration can
be performed through the existing harness. It does not show that the mandatory
conversation was necessary, cheaper, naturally selected or superior to a
single-model solution.

## What the four-bug pilot cannot estimate

The interface exposed neither a complete token ledger nor billed dollar costs.
These fields are stored as null, including cost per assigned and resolved task.
Root-observed start/completion timestamps are delayed batch envelopes containing
scheduling and orchestration; they are not reported as comparable model latency.
No quantitative savings claim can be drawn from these measurements.

Four historical bugs, two repositories, one attempt per condition, soft
filesystem isolation, potentially contaminated tasks, task-order effects and
opaque hosted model versions prevent a frontier or statistical noninferiority
claim. There is no trained existing-router comparison, no open-weight local
model result, no learned communication policy and no evidence of longitudinal
improvement. The matrix is useful evidence about feasibility and failure modes,
and the dialogue check validates a mechanism. The four-bug pilot does not test the principal economic hypothesis.

## The resource constraint behind the 95-percent target

For the follow-up target, let $C_S$ be all independent controller inference,
$C_H$ routing and handoff overhead, $C_E$ specialist inference, and $C_L$ the
matched Sol-only total. The cost requirement is

$$C_S+C_H+C_E\leq 0.05C_L.$$

Thus the available specialist budget is at most
$0.05C_L-C_S-C_H$. If that quantity is negative, selecting fewer consultations
cannot suffice: the controller itself must become more efficient, or the target
must be reported as unattained. When it is positive, assistance must concentrate
on cases where its expected verified benefit justifies that remaining budget.
A small model's low per-token price alone therefore does not establish the
system-level saving. Long histories, repeated failed attempts, selected context,
expert replies and integration all count. The independent cheap baseline and
the matched expensive baseline are essential to interpreting the frontier.

## A development case about verification and handoff

The Django `13297` issue illustrates the distinction between solving, checking
and deciding to consult. The original continuing-conversation controller chose
no expert call, removed lazy wrappers from URL parameters and reported three
narrow public tests passing. Independent official grading found the requested
regression repaired but two existing-behavior checks failing. The fresh-thread
expert condition also chose no consultation and failed the same existing checks;
its summary instead reported that its attempted test commands could not run.
Those visible-check descriptions are model self-reports. The official failures
come from the separate evaluator and were not returned to either controller.

On the same issue, the one-way controller inspected the implementation and
existing warning contract, then asked for a minimal fix before changing files.
Its selected context explained the database-binding failure and the requirement
that warnings remain deferred until values are accessed. The specialist
suggested moving wrapping into `get_context_data()`, rather than removing the
existing behavior. The controller integrated a repair and the official grade
passed. This is an observed early, context-informed consultation, not a
multi-round conversation or a verified fallback after a failed local repair.

The matched Luna-only and Sol-only runs also passed this issue. The case thus
does not establish that specialist help was necessary, or that requesting help
would have rescued the failed trajectories. It instead motivates the subsequent
shared verification instructions and explicit handoff policy. Treating every
unassisted failure as a missed delegation, or feeding hidden grading failures
back into the live controller, would overstate the evidence. A causal rescue
experiment would need separately registered continuations from matched
predecision states, with all extra inference counted.

## Measured context-only interface overhead

The separate specialist-interface calibration produced the following native
counter observations. Each row is one fresh Sol call on the same arithmetic
question; both reported zero cached-input tokens and no tool events.

| Context-only interface | Input tokens | Output tokens | Published-rate USD |
|---|---:|---:|---:|
| Default instructions | 10,481 | 85 | 0.021812 |
| Compact role instructions | 6,393 | 100 | 0.013786 |

Input fell 39.0% and the published-rate model-cost scenario fell 36.8%. Both
answers were correct for the declared arithmetic fixture. The modest output
length difference is stochastic variation from one draw per interface; these
observations provide no accuracy-retention estimate for repository tasks. They
identify removable fixed context as a practical cost component and motivate a
separately graded development candidate. The reduction cannot be extrapolated
to long questions, cached sessions or complete assisted tasks without their own
measurements. No invoice or subscription-quota saving is inferred.
