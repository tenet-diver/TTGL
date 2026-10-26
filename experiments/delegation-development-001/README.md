# General delegation policy development

The shared development set is the first four original engineering-panel tasks.
Their original outcomes were already observed. These are development cases,
never the held-out evaluation. The 12 reserved cases in
`../delegation-heldout-001/tasks.json` are disjoint.

Three candidates each receive four tasks in three conditions: Luna-only,
Sol-only and assisted Luna. All acting agents receive the same v2 independent
solving and verification guidance. Each candidate has 12 new assignments, for
36 total. Every candidate and its independent controls remain reported.

| Candidate | Controller decision policy | Context-only expert interface |
|---|---|---|
| adaptive-001 | Evidence-driven reassessment; early consultation permitted | Default Codex instructions |
| fallback-001 | Bounded independent attempt and verification; fallback after unsuccessful repair | Default Codex instructions |
| compact-001 | Same adaptive policy | Compact role-specific instructions |

`selection-protocol-002.json` is the active selection registration. It adds the
compact candidate before any v2 development grades or held-out inference. The
original `selection-protocol.json` is preserved. Selection prioritizes assisted
resolution count, then absolute total model-cost scenario, with a deterministic
lexical tie-break. The selected policy and its source hashes are bound before
held-out inference. This development search does not establish generalization.

The compact interface uses the documented `model_instructions_file` setting
only for context-only roles. Acting controllers, permission profiles, native
tool exclusions, schemas and resource budgets are unchanged. Its separate
[two-call calibration](../../results/compact-expert-calibration-001/analysis.json)
recorded 39.0% fewer input tokens and 36.8% lower published-rate scenario cost,
with both arithmetic answers correct and no tool use. That mechanism check is
not a repository-task accuracy result. See the
[official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

The original 72-assignment study is unchanged. New studies use the same pinned
validated environments. Their grader caches are seeded from archived exact
program reports only when evaluator image, full grading dataset and timeout
match. Each hit also verifies the full patch and native report; no model attempt
or token count is reused. Reuses are recorded separately from test executions.

Study files and positive native-token preflights are in
`../../results/delegation-development-001`. Inspect actual finalized manifests
and official grades for execution progress. Frozen designs and preflights do
not constitute scored outcomes.
