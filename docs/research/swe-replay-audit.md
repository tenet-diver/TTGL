# Independent audit of the SWE-bench replay and continuation tooling

Reviewed 26 October 2026 by a separate analysis agent. This audit inspected the
implementation and independently recalculated the archived numerical results;
it did not run new models or audit provider invoices.

## Result

The replay's primary numerical conclusion is reproducible and negative for the
joint hypothesis. On all 500 SWE-bench Verified tasks, the fixed 50% large-model
allocation resolves 321 issues (64.2%), versus 364 (72.8%) for GPT-5.2 high. Its
selected historical inference estimates total $127.56669275, versus
$236.78350885 for the reference: $0.2551333855 per assigned task and **46.125%
less estimated inference cost**, with an **8.6 percentage-point quality loss**.
That does not satisfy the proposed three-point quality tolerance.

The two-sided conditional task-bootstrap interval for quality difference is
approximately −11.605 to −5.6 percentage points. The repository-cluster
sensitivity also excludes the allowed loss. This is evidence against this
particular pre-task routing policy's joint target, not against every possible
conversational architecture.

Expected random routing at the same 50% allocation reaches 64.5%, compared with
64.2% for the learned policy. The additional descriptive comparison gives a
router-minus-random difference of **−0.3 percentage points**, with a conditional
95% task-bootstrap interval of **−2.4 to +1.9 points**. The selected-inference
cost ratio is 0.9798 (95% interval 0.8835–1.0759). The auditor independently
recomputed both point estimates and intervals from the task records. Neither
comparison demonstrates a learned routing advantage. The random comparator is
an analytical expected mixture; these intervals do not include variability from
a newly realized random allocation.

## Independently verified checks

- Recomputed every one of the 61 policy summaries from `task-records.jsonl`,
  including success counts, total selected cost and savings ratios. All agree.
- Verified 500 unique tasks, 12 repositories and complete outcomes/cost fields
  for ten models: 5,000 historical task-model observations. Failures remain in
  the denominator and their reported costs remain in totals.
- Reconciled all ten success rates and total costs with the source metadata.
- Checked all 522 cached public source files against the archived byte hashes,
  and checked protocol, script, summary, sources and task-record hashes against
  the run manifest.
- Checked that each of five folds has 400 training and 100 test tasks, with no
  overlap, and that every primary fold allocates exactly 50 tasks to the larger
  model.
- Inspected feature fitting: TF-IDF vocabulary, length scaling and repository
  encoding fit on training tasks only. Quality and cost estimators receive only
  training labels/costs. Held-out choices use predictions and public issue text,
  not their own realized cost, success, trajectory, patch or test results.
- Inspected the within-fold quota implementation. It avoids the indirect
  cross-fold label dependence that a single global rank of out-of-fold scores
  could introduce. It is a batch policy, not an online quota guarantee.
- Checked that only explicitly named nondeployable oracles use held-out
  outcomes and costs, and that the model/utility grid is reported rather than
  silently replacing the primary policy with its best observed member.
- Ran the new benchmark, subscription and personal-harness software tests:
  **81 passed** at this review stage. These are software tests, not additional
  model-performance observations.
- Independently recalculated the two highlighted supplemental comparisons in
  `additional-comparisons.json`, including the same 2,000 seeded paired
  bootstrap resamples. Their quality and cost intervals agree exactly within
  numerical precision. These comparisons were added after the initial analysis,
  without refitting the routers; they are descriptive, not a new primary test.

The integration lead's subsequent full-suite run reports **136 passed, one
skipped and two subtests passed**. The earlier 81-test count above records this
audit's initial subset execution, before the subsequent corrections and tests.

The audited replay script SHA-256 is
`2a70188ca0024acdaee925b55677802139fd611134ba26eeb4b55b1a8fe3f1aa`.
The frozen protocol SHA-256 is
`ddf64c54c3c15f9f8039491cf7774c83fec2632c7a281b393ce2fb48c75f0a1e`.

## Economic and statistical limits

These are **upstream-estimated inference dollars from February 2026
submissions**, not new measured provider bills, current model prices, full
operating costs or Codex subscription usage. Applying selection to existing
standalone trajectories does not run the selected agents again and does not
simulate bidirectional communication. No subscription savings can be inferred
from this replay.

Two Gemini records (`django__django-15731` and `django__django-15814`) report
zero cost despite one API call each and an unresolved outcome. The replay
preserves those published values; the auditor cannot establish whether zero is
a complete cost measurement. The primary GPT pair has no zero-cost rows, so its
result is unaffected. Portfolio and oracle calculations inherit this source
uncertainty.

The task bootstrap conditions on the fitted out-of-fold policies and the
published one-attempt matrix. It does not refit the router or estimate fresh
agent sampling variability. The cluster sensitivity resamples only twelve
repository clusters; it is not a repository-unseen evaluation. Related issues
and public-model contamination remain concerns. Aggregate results were inspected
before selecting this secondary analysis; the freeze is not prospective
registration of a fresh model trial. Grid confidence statements are exploratory,
with no familywise guarantee for a selected winner.

A strong inexpensive fixed-model baseline matters. The same records give
MiniMax M2.5 75.8% resolution at $0.073289987844 per task. Some portfolio policies
look favorable relative to GPT-5.2 while costing more than this fixed model. For
example, the ten-model portfolio at lambda 0.25 reaches 76.2%, a **+0.4-point**
difference from MiniMax (95% interval **−0.8 to +1.6 points**), while costing
**1.574 times** as much (95% interval **1.398–1.762**). This is not a demonstrated
quality improvement over the cheaper fixed backend. MiniMax was highlighted
after inspecting the single-model results; the supplemental report explicitly
preserves that selection limitation.
Any claim that routing adds value should compare with a development-selected
fixed backend as well as the expensive reference. The `os_model` field is an
upstream metadata tag, not an independent license audit or proof of on-device
execution.

## Continuation tooling review

The benchmark bridge preserves frozen source/task identities, fresh repository
revisions, randomized paired assignments, standard prediction files and exact
submitted-patch hashes. It refuses inference before a positive native metering
preflight and refuses silent replay of ambiguous in-flight turns. Analysis
requires every assigned manifest rather than dropping missing assignments.
Unpriced model usage remains unknown. Input-cache and reasoning counters are
not added twice. Official grade imports bind the report to the exported patch.
For an exactly empty submitted patch, the importer accepts only the explicit
`empty_patch_ids` and `submitted_ids` category in the official aggregate report,
and requires that the task is not listed as resolved. The auditor checked these
field names and behavior against the pinned official `reporting.py` and ran all
**15 benchmark bridge tests** after this addition; they pass.

The two added ablations preserve the controller thread and the same turn/time
limits while starting a fresh expert thread for every consultation. `oneway`
permits only the structured `answer` action and instructs the expert not to ask
clarification; `reset_expert` permits clarification/challenge without retaining
expert state. The existing `personal` condition retains expert state. Fresh
expert usage is counted separately and reused expert identities are rejected.
This is not a complete two-by-two factorial of memory and direction: the
one-way versus persistent comparison changes both. The reset-expert arm helps
separate those effects, and actual messages must still be audited because
natural-language questions cannot be ruled out by an action enum alone.

The subscription collector uses supported app-server initialization followed by
per-thread `account/usage/read`, never an account-wide history request or a
model-inference method. Its output drops unrelated account summaries and raw
diagnostics. It requires independent-root attestation before summing thread
estimates, avoiding an unsupported parent/child accounting assumption.

One completeness defect was identified and corrected during review: a terminal
task with an unidentified failed invocation could have known earlier thread
estimates summed by the standalone collector. The benchmark importer already
rejects such incomplete task accounting. The collector now records ledger
completeness separately from terminal status, preserves available per-thread
observations and returns unknown totals when the selected state has accounting
issues. The auditor inspected that correction and independently ran all **15
subscription tests**, including the new end-to-end regression for a terminal
failed task with one known thread and one unidentified invocation. They pass.

These checks do not establish a successful authenticated Codex inference run
in the current managed environment. The native startup remains blocked by its
read-only state directory. The auditor also inspected the actual bridge attempt
in `results/codex-runtime-20261026/blocked-study`: preflight readiness is false,
the first preflight manifest is failed, every usage field and dollar cost is
unknown, and no scored assignment directory exists. This is preserved runtime
failure evidence, not a new benchmark or zero-cost model result.
Host-based solver checkouts also do not themselves
provide official task dependencies or hardened separation from evaluator
artifacts. Passing reference-fix controls, actual worker environments and
correct evaluator/image provenance remain prerequisites on the next host.

## Research interpretation

This is a credible, reproducible exploratory analysis on an established
benchmark. It is not evidence that the proposed personal conversational agent
is novel or that it saves money. Learned routing and small-agent delegation
already have close prior art. A defensible thesis contribution is the controlled
replication and extension: test persistent dialogue against one-way assistance,
reset expert state, initial routing and fixed backends under matched information
and resource limits, with full costs and failed assignments retained. Positive,
null and negative findings can all be research contributions; broad architectural
priority and a novel routing algorithm are not established here.
