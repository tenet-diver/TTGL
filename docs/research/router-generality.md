# General-purpose routing, not benchmark-specific prompting

The user's explicit constraint is that Luna's router must generalize beyond the
benchmark. SWE-bench development episodes reveal failure mechanisms; they are
not the router specification. No repository names, expected patches, hidden tests,
case identifiers, benchmark-specific triggers or thresholds may enter a general
router prompt. Never tune against reserved validation outcomes.

Each prompt revision must state the observed mechanism, the domain-independent
rule, why it might help on unrelated tasks, and what evidence would falsify it.
Keep revisions bounded and versioned before fresh tasks. Gains across different
development cases cannot demonstrate causal improvement or transfer. Preserve
failures and costs, and freeze a policy before any separately authorized held-out
comparison. The existing 24 validation tasks remain untouched.

The current mechanism is stopping after acknowledging a verification gap. The
general rule is to seek discriminating evidence for current requirements, distinguish
contradictory evidence from obsolete evidence and unavailable evidence, continue
useful independent work, and ask a focused expert question when a material gap
persists. Checks should fit the task: execution, observation, calculation,
simulation or authoritative evidence. Do not force code changes or test suites
for unrelated domains. Two or three useful checked independent approaches is a
default before help, not a mandatory count of edits or retries.

V6's obsolete-test paragraph is a coding instantiation of old-versus-current
requirements, not a rule to ignore failing tests. Preserve their output, justify
why a requirement changed, and seek positive evidence for the new requirement.
Neither honest uncertainty nor a narrow passing check alone warrants stopping
while useful affordable work remains. The expert receives evidence, attempts,
lessons and uncertainty and returns advice for the acting model to verify.

Future transfer claims require a separately registered diverse task set and
appropriate task-level checks, not just additional familiar benchmark tasks.
This constraint does not authorize browsing sealed validation inputs, expanding
current inference caps, or treating software wiring tests as model-quality tests.
