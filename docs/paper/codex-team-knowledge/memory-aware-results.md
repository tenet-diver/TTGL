# Memory-aware team comparison

Status: **incomplete**, **39/56 assignments recorded**. Separate development extension; historical studies remain unchanged.

This table includes all completed cells. Rows with fewer than two libraries are incomplete subsets, not matched comparative estimates.

Measurement snapshot: 2026-11-15T16:02:26.794541+00:00.

| Arm | Capacity | Completed / planned | Verified sources | Normal parents | Mean run-end seconds | Mean actual coding threads | Mean Standard scenario credits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| native | 1 | 1/2 | 1/1 | 1/1 | 263.2 | 1.0 | 6.3842 |
| native | 2 | 2/2 | 2/2 | 2/2 | 212.3 | 2.0 | ≥8.0816 |
| native | 4 | 1/2 | 1/1 | 1/1 | 170.9 | 4.0 | ≥13.0806 |
| native | 8 | 1/2 | 1/1 | 1/1 | 170.0 | 4.0 | ≥12.4902 |
| notebook | 1 | 2/2 | 2/2 | 2/2 | 281.4 | 1.0 | 5.8426 |
| notebook | 2 | 1/2 | 1/1 | 1/1 | 178.3 | 2.0 | 7.0486 |
| notebook | 4 | 2/2 | 2/2 | 2/2 | 196.0 | 4.0 | ≥14.1166 |
| notebook | 8 | 2/2 | 2/2 | 2/2 | 265.6 | 4.5 | ≥20.1158 |
| mcp_memory | 1 | 1/2 | 1/1 | 1/1 | 332.7 | 1.0 | 6.0729 |
| mcp_memory | 2 | 2/2 | 2/2 | 2/2 | 222.6 | 2.0 | ≥8.4564 |
| mcp_memory | 4 | 1/2 | 1/1 | 1/1 | 186.8 | 4.0 | ≥16.6301 |
| mcp_memory | 8 | 1/2 | 1/1 | 1/1 | 290.4 | 4.0 | ≥15.7848 |
| mem0_luna | 1 | 2/2 | 2/2 | 2/2 | 433.6 | 1.0 | 7.7961 |
| mem0_luna | 2 | 2/2 | 2/2 | 2/2 | 660.6 | 2.0 | ≥15.2486 |
| mem0_luna | 4 | 1/2 | 1/1 | 0/1 | 482.3 | 4.0 | ≥20.6492 |
| mem0_luna | 8 | 2/2 | 1/2 | 1/2 | 480.5 | 4.5 | ≥23.4303 |
| graphiti_luna | 1 | 2/2 | 2/2 | 2/2 | 554.9 | 1.0 | 10.1353 |
| graphiti_luna | 2 | 1/2 | 1/1 | 1/1 | 552.7 | 2.0 | ≥8.9241 |
| graphiti_luna | 4 | 1/2 | 1/1 | 1/1 | 408.8 | 4.0 | ≥19.4288 |
| graphiti_luna | 8 | 1/2 | 1/1 | 1/1 | 509.1 | 4.0 | ≥21.3480 |
| smallville_luna | 1 | 1/2 | 1/1 | 1/1 | 356.1 | 1.0 | 6.1339 |
| smallville_luna | 2 | 1/2 | 1/1 | 1/1 | 262.4 | 2.0 | ≥7.4221 |
| smallville_luna | 4 | 2/2 | 2/2 | 2/2 | 374.6 | 4.0 | ≥18.3671 |
| smallville_luna | 8 | 1/2 | 1/1 | 1/1 | 521.6 | 4.0 | ≥20.3684 |
| searchable_logs | 1 | 2/2 | 2/2 | 2/2 | 218.4 | 1.0 | 6.6550 |
| searchable_logs | 4 | 2/2 | 2/2 | 2/2 | 195.3 | 4.0 | ≥16.3401 |
| searchable_logs | 8 | 1/2 | 1/1 | 1/1 | 190.7 | 4.0 | ≥16.8470 |

All model-rate amounts include recorded coding and Luna maintenance inference. Unknown requests make costs lower bounds. These are dated pricing scenarios, not cash or quota measurements. Preparation, independent replay, local compute and research overhead are additional.

[Full allowlisted measurements](memory-aware-results.json), [per-cell CSV](memory-aware-cells.csv), [protocol](../../../experiments/codex-team-knowledge-001/memory-aware-extension-protocol-001.json), [experiment appendix](appendix.md).

This two-library development matrix cannot establish a general memory-system advantage, held-out transfer or causal knowledge benefit. A passing artifact and normal parent completion are distinct outcomes.
