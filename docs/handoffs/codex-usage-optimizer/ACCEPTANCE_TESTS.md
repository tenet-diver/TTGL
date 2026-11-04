# Acceptance tests for the implementation

Package validation is separate; these are requirements for the product to implement.

| ID | Scenario | Expected behavior |
|---|---|---|
| T01 | ccusage-only aggregates | Session findings allowed; command-level claim marked needs_evidence |
| T02 | Cumulative usage 100 then 250 | Total 250, not 350; authoritative grain recorded |
| T03 | Overlapping imported/live/archived event | One counted source identity; uncertainty retained for ambiguous duplicates |
| T04 | Raw output differs from truncated model-facing output | Separate values and provenance, no inflated payload claim |
| T05 | Missing duration/cache data | Null and missingness, no fabricated zero |
| T06 | Tool log contains executable instructions | Treated as quoted data; never executed |
| T07 | Command normalization with meaningful arguments | Distinct operation families not falsely merged |
| T08 | Quiet reporter hides failure diagnostics | Trial fails and proposal is not adopted |
| T09 | Smaller output but more debugging turns | Whole-task metrics show overhead; no output-only success claim |
| T10 | Parallel tool durations overlap | Work-time and critical path shown separately |
| T11 | User accepts version 2 but file preimage changed | Executor rejects stale action and prepares a new reviewable diff |
| T12 | Repeated Accept / API retry | One decision/trial identity; no duplicate change or paid trial |
| T13 | Declined proposal is reworded | Same fingerprint remains suppressed |
| T14 | New evidence materially changes a declined proposal | New version explains changed evidence and may reappear |
| T15 | Two recommendations overlap same output region | Savings not summed; conflicts/combined trial explicit |
| T16 | Local-only import/analysis selected | No cloud upload or implicit external LLM call |
| T17 | User edits file after trial | Rollback does not overwrite new edits; reverse diff requires resolution |
| T18 | Final suite required by repository | Narrow exploratory runs do not remove final verification |
| T19 | Imported old logs lack timing/outcome detail | Coverage limitations remain visible in UI and report |
| T20 | Estimate based on assumed 60% reduction | Labeled scenario, not statistical confidence or measured savings |
| T21 | Local UI accepts proposal without concrete patch | Block acceptance or show preparation action; no hidden mutation |
| T22 | Analyst logs are included in source history | Target activity and optimizer overhead separated without erasing spend |
| T23 | Unknown installed tool flag | Proposal blocked pending help/version verification |
| T24 | Detector proposes removing an unused MCP server | Check actual schema exposure and representative required tasks first |
| T25 | Agent loses required detail after compression | Revert and retain exact archive; quality gate fails |

Recipe catalogue validation checks exactly 100 unique IDs and distinct titles, complete trigger/change/check/risk fields, null default savings, and progressive-disclosure lookup. Reference script tests check eligible grouping, explicit scenarios, missing/zero estimates, negative input rejection, no failure-call inclusion, and JSON-schema conformance. UI prototype tests inspect Accept/Decline/Later and decision export without pretending a backend applies changes.

Real pilot: import a chosen historical sample, compare source totals and displayed evidence, identify a few large repeated opportunities, and execute one accepted reversible change on an isolated task with both passing and failing diagnostic fixtures. Document real coverage, tool versions and overhead. No success or numerical reduction is assumed in advance.


## Version 1.1 history/comparison requirements

Implement H01–H16 in OPTIMIZATION_HISTORY.md, covering independent state dimensions, retained rejection history, idempotent receipts, stable tool IDs, exposure-aware cohorts, missing values, zero baselines, negative effects, overlapping techniques, runtime activation, safe SQL, evidence gates, result revisions, manual changes and rollback. The executable synthetic query tests below verify aggregate semantics, not the production state machine.
