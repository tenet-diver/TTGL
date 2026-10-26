# Frozen exploratory public SWE-bench Verified replay

The completed analysis is in [`results/swe-replay-001`](../../results/swe-replay-001/README.md).

`protocol.json` was frozen before fitting the router, after inspecting public aggregate accuracy/costs to select the data. `freeze.json` verifies its bytes. This is an exploratory secondary analysis, not a prospective registration. The 500 official task IDs are paired across ten published mini-SWE-agent 2.0.0 configurations; no model calls are made by this replay.

The primary pair is GPT-5-mini versus GPT-5.2 (high), with a fixed 50% large-model quota and five-fold held-out prediction of success and cost. Every held-out fold ranks its own predictions so another fold's training does not indirectly expose this fold's labels through a global quota. All fractions and utility values were specified before fitting. Repository-level cluster bootstrap is a sensitivity analysis, not an unseen-repository validation split.

Primary hypothesis check failed: the fixed policy saved 46.1% of historical estimated inference cost but lost 8.6 percentage points of resolution accuracy. Attractive portfolio comparisons against GPT-5.2 are insufficient evidence for routing: the planned standalone MiniMax 2.5 control is cheaper and nearly as accurate as the discussed portfolio point. The latter comparison is preserved as additional descriptive analysis after observing the full table.

Reproduce with `scripts/swe_public_replay.py` and generate the supplementary table/comparisons with `scripts/swe_replay_report.py`. All original outcomes, fitted predictions, source hashes, exact folds, cost sensitivities and negative findings are preserved. Costs exclude router and environment overhead; source-estimated inference dollars are not Codex subscription credits or cash savings.
