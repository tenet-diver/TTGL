# Native Codex teams and shared knowledge

Read the [paper](paper.md) and [completed 24-run pilot](pilot-results.md), with
[CSV](pilot-cells.csv), [sanitized results](pilot-results.json) and
[standalone plots](figures/pilot-scaling.pdf). The prospective draft preceded
inference. All pilot cells are complete; reserved-library evaluation is pending.

All 24 artifacts pass independent replay on two development libraries. Native
capacity eight is 31.3% faster on average with at least 2.45× the fully measured
single-agent model-rate cost, using four or five actual threads. Added knowledge
has mixed timing and no observed completion gain. MCP agents publish 91 observations
but all four read queries are empty. Incomplete streams leave 17 cells with cost
lower bounds, not known totals. These are exploratory results, not a broad
scalability or innovation claim.

The [preparation record](preparation-results.md) preserves failed local-provider
checks, admission boundaries and unknown usage. Earlier studies and paused
research schedules remain unchanged.

The [reserved-library extension](reserved-extension.md) freezes 80 assignments on
five admitted libraries, crossing native capacity, added MCP memory and explicit
knowledge-use guidance. Its results remain pending.
