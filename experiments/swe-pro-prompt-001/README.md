# Small-subset proprietary prompt study on SWE-bench Pro V2

Status: public inputs reserved on 27 October 2026; **no controls or model trials
have executed**. This does not authorize an automatic full benchmark run.

The official V2 release has 642 tasks across 11 repositories. To contain prompt
iteration expense, use 12 development tasks and 24 separate validation tasks.
`reservation.json` pins the upstream revision, seed, exact IDs and public-input
hashes. Selection round-robins repositories in seeded order, then draws tasks by
seeded hash order within each repository. It uses no model outcomes. This
repository-balanced sample is not proportional to the full benchmark mix;
report it as a subset study, with repository-level results.

Only public instructions, task configuration and environment Dockerfiles have
been acquired. Evaluation tests and reference patches must stay outside model
workspaces. Use the maintained upstream Harbor harness and locked protocol;
do not write a substitute evaluator or assume our Verified adapter works on Pro.

The first budget unit is environment and adapter validation, followed by one
complete development task block. Record actual token usage, provider estimates
when available, runtime and grading overhead before starting the remaining
blocks. Do not extrapolate runtime or bills from the small Verified pilot as
though already measured on Pro. A failed or ambiguous assignment is preserved;
it is not silently retried or replaced.

Each prompt candidate receives the same task set and matched Luna-only control
with its common solving/verification instructions. Sol-only uses the same public
task context and tools. Start with the existing adaptive and bounded cheap-first
policies; freeze prompt hashes, time/tool budgets, model IDs and pricing before
scored calls. If common prompts are identical, shared controls may be reused only
as explicitly registered identical assignments, never as best-of repeats.

Primary plots: task resolution versus total model-cost scenario per assigned
task; cost and accuracy relative to matched Sol; assisted versus matched Luna
successes/losses; expert calls and their timing. Include failures, controller
tokens, expert replies and integration. Inspect whether help is evidence-driven
and whether integration is verified; success alone does not establish necessity
or optimality of a call. Preserve paired uncertainty and avoid treating a tiny
panel as proof of 95% population retention.

Select a policy on development only, freeze it, then evaluate once on the reserved
24 tasks with matched Luna-only and Sol-only controls. Validation results must not
feed prompt updates while continuing to be called held-out. Larger samples are a
later budget decision, not a prerequisite for each prompt iteration. Open-weight
replication, distillation and RL follow this proprietary comparison.

Sources inspected:
- [Official Pro V2 harness and protocol](https://github.com/scaleapi/SWE-bench_Pro-os/blob/66f92766bba642462d4bbe5479e83f91f9211862/v2/README.md).
- [Official dataset card](https://huggingface.co/datasets/ScaleAI/SWE-bench_Pro/blob/main/README.md).

Preparation: `python scripts/prepare_swe_pro_subset.py --output NEW_DIRECTORY`.
