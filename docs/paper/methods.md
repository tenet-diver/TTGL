# Experimental design

## Conditions and estimands

The unit of analysis is an assigned repository issue, not an individual model
call. Every registered issue is assigned to every primary condition. Each run
starts from a clean copy of the same buggy revision and receives the same issue
description, relevant memory, editable source boundaries and visible tools.
The primary conditions are:

| Condition | Behavior | What it estimates |
|---|---|---|
| S: single controller | Luna acts and verifies without model assistance | Controller's independent capability |
| L: single expert | Sol acts and verifies throughout | Same-context strong-agent reference |
| R: pre-call routing | A task-only Luna decision selects S or L, then a fresh selected agent acts | Initial allocation without adaptive collaboration |
| C: conversational routing | Luna acts, exchanges up to two expert turns with Sol, then verifies and integrates | Added effect of adaptive expert conversation |

R is a prompt-based routing baseline. It is **not** a reproduction of RouteLLM,
Router-R1, MasRouter or EdgeWise. Those methods require their own eligible model
pairs, learned parameters, training data and runtime assumptions. Reusing a
router calibrated for a different pair without validation would not establish
its performance on Luna and Sol. Native implementations, where available and
licensed, enter a larger study as separately named arms.

The C-versus-L contrast tests the complete product architecture. C-versus-S
tests whether access to help is useful. C-versus-R tests adaptive consultation
against initial selection. None alone identifies the value of personalization,
because all primary conditions share the same memory. That value requires the
memory and skill ablations below. Sol may be replaced by Astra or an open-weight
expert only as a separately versioned comparison; outcomes are not pooled under
the vague label “large model.”

## Engineering pilot

The pilot uses genuine historical Python bugs from the public BugsInPy corpus [@ttglbugsinpy2026].
A deterministic feasibility screen checks candidate bugs in the registered
order before any candidate-agent outcomes are observed. A usable task must have
a buggy revision that fails its regression check and an official fixed revision
that passes it under the recorded environment. Every compatibility exclusion is
retained. If a harness adaptation is necessary, its exact change and rationale
are recorded; the pilot does not inherit the official BugsInPy leaderboard's
meaning merely by using its bugs.

Task descriptions can be derived from the behavior exercised by an upstream
regression test when a self-contained issue statement is unavailable. This is
recorded as a derived task prompt, not presented as an untouched benchmark
instance. Reference patches and grading fixtures are kept outside the worker
copy, with the shared-filesystem limitation stated above. Small historical fixes
provide a useful execution check but may have a ceiling effect and may already
be present in model training data.

The task list, source revisions, prompts, constraints, baseline checks, grading
commands and analysis design are frozen before the live trials. Model settings,
fresh-session identifiers, selected routes, expert requests and submitted patches
are archived. The same task cannot be silently rerun until it passes. An
infrastructure retry is separately identified and preserves the first attempt.
Completed and failed assignments remain in the denominator. The feasibility
screen is independent of the models being compared.

In the personal condition, expert responses contain only the context provided
by the controller and their resulting proposal. The pilot limits assistance to
the registered number of consultations. A controller may choose zero calls.
Baselines receive the same task time envelope; the personal condition's budget
includes its expert waiting and integration time. These are wall-time controls,
not claims of equal token consumption. Model reasoning-effort settings are
recorded, and the unobserved internal compute differences remain a limitation.

The pilot is developmental. Its issues, outputs and human observations are
excluded from later training/calibration/test claims that require unseen
examples. It establishes that the architecture can be executed and independently
graded, and identifies measurement or orchestration failures. It cannot prove
noninferiority, cost superiority, architectural novelty, long-horizon learning
or a benefit for open-weight local models.

## Metered benchmark engineering panel

A separate desktop protocol extends the feasibility work to the frozen
12-issue SWE-bench Verified panel. It assigns each issue once to six conditions:
Luna alone (`small`), Sol alone (`large`), task-only selection (`precall_router`),
one-way expert assistance (`oneway`), a fresh expert thread for each
consultation (`reset_expert`), and continuing expert conversation (`personal`).
The latter two have the same expert-call allowance; retaining conversation is
the intended contrast. No consultation is compulsory. Actual requested and
completed expert turns are reported, including unsuccessful requests. This is
an engineering panel, not the powered confirmatory study specified below.

The requested identifiers are `gpt-6-luna` and `gpt-6.1-sol`, both at medium
reasoning effort. These hosted identifiers do not disclose parameter counts or
immutable weight revisions. Every condition has the same 900-second solver
budget, including its routing and expert work. The bounded controller has up
to six outer turns and two expert consultations, with at most 24,000 selected
context characters. All conditions start with the same empty personal memory.
No weights, router parameters, procedural skills or user memory are learned
from scored outcomes. Task order follows the frozen panel; condition order
within each task is randomized with seed 1729. This task grouping amortizes
image loading without sharing worker files between conditions.

Each acting agent receives a disposable Docker worker with no host mounts,
network, Docker socket or retained prior-agent checkout. It has two CPU cores,
a 4-GiB memory limit and a 256-process limit. The ordinary authenticated Codex
client remains on the host, with native host tools disabled. Its repository
shell tool uses the official MCP SDK to execute only in that assigned worker.
Routers and experts receive no worker tool; expert context is selected by the
controller. Original image Git history is replaced with an exact-base shallow
checkout. Tracked source is checked by blob identity, audited build metadata
is restored, and the staged working tree must be clean. Ignored compiled
extensions remain available for scientific packages. Exact image identities,
source hashes and setup exceptions are retained.

Before scored inference, all 12 original environments pass independent official
controls: a neutral-marker no-fix submission leaves the regression unresolved,
and the supplied reference patch resolves it. Both are evaluated with the
unchanged pinned SWE-bench harness. All 12 staged solver environments also pass
fixed public smoke modules. Failed preparations and their dependency repairs
remain archived. Eligibility is determined before model outcomes; no task is
replaced. The original public/private panel hashes are retained, and the
trusted grader's dataset copy changes only its image references to the exact
validated image identities. Grading material is outside every solver worker.

Every exported submission is joined by its exact patch hash to an original
official report. Byte-identical programs for the same task may share that
report only when evaluator image, private dataset and timeout also match.
An explicit reuse receipt distinguishes this from a fresh evaluator execution.
Different patches receive fresh run identifiers. The grading timeout is 1,200
seconds in every condition; the solver budget remains 900 seconds. Functional
resolution follows official grading. The older pilot's additional strict
artifact-policy outcomes are reported separately and are not relabeled as
SWE-bench results. Failed assigned attempts stay in the denominator, and an
uncertain or unmetered attempt is not silently retried or priced at zero.

The study freezes the published Enterprise Codex Standard-mode token rates
before scored inference [@openaiCodexRateCard2026]. Per million tokens, Luna's
uncached input, cached input and output rates are US$0.10, US$0.01 and US$0.50;
Sol's are US$2.00, US$0.10 and US$10.00. Native total input includes cached
input, so only uncached input receives the ordinary input rate. Native output
already includes reasoning. Every routing and expert role contributes to the
assigned condition, and its per-model counters must reconcile to the task
total. Unavailable counters remain unavailable costs.

These rates define a counterfactual published-token-rate scenario, not this
account's subscription invoice, quota consumption or an API bill. The rate
card's signed-in Codex long-context policy applies to that scenario. API
cache-write and request-level context billing need a separately compatible
meter. Provider-estimated credits and dollars, when available, are separate
observations. Preparation time and actual grader executions are recorded;
hardware, energy, setup, grading and subscription allocation are not assumed
to cost zero. A favorable token-rate comparison alone cannot establish the
proposed full-cost target. Paired task bootstrap intervals are conditional on
this small public panel and cannot establish a three-point quality margin.

## Confirmatory software-engineering study

The proposed primary evaluation uses a pinned release of SWE-bench Verified,
with the official evaluator and recorded image digests [@jimenez2024swebench; @swebenchverified2024]. Development data come
from disjoint issues and bug clusters; a repository-unseen analysis additionally
excludes all development data from its registered repositories. Public benchmark
exposure and opaque model training data remain contamination risks, so a
prospective private or newly released issue replication is desirable.

For each task, accepted success is functional resolution **and** satisfaction of
feasible prespecified mandatory constraints. Resolution and constraint adherence
are also reported separately. A requirement such as preserving a public API or
avoiding new runtime dependencies must be machine-checkable or independently
reviewed under a frozen rubric. Requirements are screened for consistency with
the task before outcomes are observed. Hidden constraints that the agent was
never told are not introduced after submission.

The proposed primary gate is C-versus-L quality noninferiority with a margin of
three absolute percentage points, followed by superiority in mean total cost per
assigned task. A 25% reduction is the proposed practical target; both its point
estimate and uncertainty must be reported. These thresholds are prospective
design choices and are not fitted to pilot outcomes. The margin is an explicit engineering tolerance, not a universal
customer preference. It must be approved in the protocol freeze before held-out
execution. A failed noninferiority test is inconclusive about equivalence. A
claim of improved quality is a separate, multiplicity-controlled test, not an
alternative success criterion chosen after seeing results.

Three recorded repetitions per task are planned for the fully funded study.
Repeated seeds remain nested within tasks. Paired task-weighted effects and
repository-clustered uncertainty are reported with a conditional-on-repositories
sensitivity analysis. Sample-size planning uses development-only discordance,
variance and cost observations. The full matrix is not assumed to fit the
US$100 Runpod pilot allocation. A dated resource plan must include failed runs,
container evaluation, model loading, artifact storage and cleanup before that
study starts.

## Ablations needed to explain an effect

The essential conversational ablation is **one-way assistance versus continuing
two-way dialogue**. In the former, an expert returns a bounded proposal and does
not ask clarification questions; in the latter it can ask, challenge and revise
in the same thread. Match the expert pool, permitted context and total budget,
and report actual turns rather than forcing a conversation on every easy task.
A third version resets expert state between requests, separating retained
conversation from simply spending more inference. This contrast is a testable
extension, not a universal claim of priority over all prior multi-agent work.

Memory, cooperation and learning are different interventions. The follow-up
matrix therefore includes no personal memory, correct matched personal memory,
generic project guidance and shuffled-user guidance. Shuffled material uses
synthetic profiles and is an experimental control, never a product behavior.
The generic-skill baseline is especially important because prior personalization
research reports that pooled skills can outperform personalized skills.

Within the cooperative condition, compare task-only expert selection with
small-first consultation, full permitted context with selected context, and
expert-only completion with controller integration. Verification ablations can
remove additional controller critique while preserving the independent final
grader. They cannot give one condition access to hidden tests. A manager-only
condition tests coordination without local work; it is not the flagship
personal-agent treatment.

Expert competence and extra inference are potential confounds. Use the same
expert backend across conditions, retain router/manager overhead, and include a
large-controller-with-the-same-expert option when studying controller size.
An equal-total-budget single-expert condition tests whether extra thinking by
one model explains an apparent multi-agent advantage. Expanded expert portfolios
are added after the dyadic comparison, with pool size and expertise held fixed
within each contrast.

## Learning collaboration without reinventing distillation

Classical sequence or logit distillation is background and an optional component,
not the central experiment. The learning question concerns the personal agent's
collaboration policy. Start with frozen weights and versioned procedural skills;
compare no update, factual-memory-only update, generic skill update and
personalized skill update. The development curriculum presents tasks in a fixed
order and evaluates later disjoint tasks at frozen checkpoints. Evaluation
feedback never modifies a policy during its final test.

For a weight-learning replication, use a maintained agent-training framework
such as Agent Lightning rather than building a new RL trainer. Pin its release,
instrumentation boundary and training data. The initial compatible open model
and runtime must be validated independently; the hosted Luna pilot provides no
access to Luna weights and does not train that model. A Runpod key alone cannot
make hosted-model fine-tuning available.

A transparent reward decomposition is
$r=Y_{\mathrm{accepted}}-\lambda C-\mu V-\nu B$, where $C$ is measured resource
cost, $V$ counts registered constraint violations and $B$ penalizes budget
violations. Coefficients are selected on development data and frozen. If only
call counts are available, the objective is labelled a call-count penalty,
not a monetary-cost objective. Task tests provide executable feedback; this is
not automatically RLAIF. AI feedback requires a declared judge, rubric, blind
human audit and reward-hacking checks. It may supplement task tests, not replace
independent functional evaluation by assertion.

Credit assignment should compare continuing locally, asking with different
context packages and choosing different experts from the *same predecision
state*. Those extra rollouts incur acquisition cost. Future expert replies and
hidden grader results cannot enter the features available to an earlier
delegation decision. Evaluate held-out accepted success, unnecessary and missed
delegations, context sufficiency, recovery success and full amortized cost. A
falling expert-call count is valuable only when quality and constraints remain
satisfied. No monotonic learning curve is assumed.

## Persistent many-to-many extension

A swarm adds persistent worker memories, task ownership and communication
topology to the decision problem. It is a separate extension, since improved
group performance can otherwise be attributed to more models or more inference.
Begin with fixed roles and durable task identifiers. Compare a star centered on
the personal agent with a bounded peer graph and a learned communication graph,
under equal total token, tool and time caps and the same expert pool.

Measure accepted team output, duplicate work, lost handoffs, stale-memory errors,
message volume, context disclosure and recovery after an agent restart. Role
specialization must improve held-out performance and transfer across goals to
count as useful emergence. A visually interesting conversation pattern is not
evidence. Learning can use centralized training with decentralized execution,
but rewards and credit attribution must be specified. This extension remains
prospective and does not delay or inflate the claims of the core dyadic study.

## Evidence-driven delegation as a general policy

A useful delegation policy must transfer beyond benchmark repair. The controller
first identifies the requested outcome, relevant constraints and observable
acceptance criteria. It attempts work independently while that produces useful
progress, then reassesses when checks fail, evidence conflicts, assumptions
remain unresolved or progress stalls. Early consultation is permitted when the
capability gap is apparent or an independent attempt would consume the resources
needed for integration. A failed check is evidence to interpret, rather than an
automatic trigger: an intentionally failing regression test can be part of a
successful diagnosis. Missing access or permissions must not be misclassified
as a reasoning problem that a larger model can fix.

The handoff conveys the goal, constraints, relevant artifact excerpts, attempted
approaches, observed outcomes and a specific request. Observations are separated
from hypotheses. Since a context-only expert cannot open the controller's files,
necessary content must accompany the request. The controller remains responsible
for integration and verification, and can return new evidence to the expert.
The general mechanism applies to tests in coding, source checks in research,
recalculation in quantitative tasks and acceptance criteria in planning. The
software benchmark measures one application; it cannot establish cross-domain
transfer by itself.

The prompt-development treatment gives standalone and assisted controllers the
same independent-solving and verification instructions. Assisted controllers
add either evidence-driven consultation or a simpler bounded cheap-first fallback
rule. This separates stronger ordinary prompting from the marginal value of
expert access. Development runs are disclosed separately, including failed
policies; cases whose outcomes informed revisions cannot become the final test
set. Forced consultations remain mechanism checks, because they cannot establish
that a controller chooses assistance appropriately.

Before the follow-up experiments, the practical target was sharpened to a
model-cost ratio of at most 0.05 and accuracy retention of at least 0.95 relative
to a matched Sol-only controller. Retention is the ratio of aggregate success
fractions, not an absolute five-percentage-point margin. All controller,
consultation and integration model inference belongs in policy cost. This target
is separate from the earlier prospective three-point/25-percent gate and is not
a post-hoc claim about historical replay. Published standalone benchmark scores
supply external context, but cannot replace matched controls when tools, effort,
task populations or stopping rules differ.

The analysis reports both ratios, paired uncertainty, reference successes lost,
reference failures rescued and the accuracy-cost frontier. A policy meeting the
point target on a tiny panel does not establish population noninferiority;
ceiling outcomes can yield misleadingly narrow bootstrap intervals. Falling
expert usage counts as useful only when the quality constraint is retained.
