# Validation scope

Run `python3 validate_pack.py` with jsonschema installed. It validates all 100 recipes, the four schemas, typed examples, detector arithmetic/missingness/deduplication/failure exclusion, scenario bounds and checksums. Run `skill/codex-usage-optimizer/scripts/recipe_lookup.py --query "test output"` to inspect bounded recipe lookup.

The analysis JSON is synthetic, with 30,000 estimated payload tokens and a user-supplied illustrative 60% reduction scenario (18,000 payload tokens); neither is a real usage measurement or a billing forecast. One passing-call output size is unknown and excluded from that total.

The skill is packaged but not installed globally. The monitoring backend, production detectors/executor/UI and experiments are implementation work. The HTML prototype has demo-only decisions. See VALIDATION_RESULT.json for actual checks completed; no raw user logs or paid model calls are used.

Completed checks: skill frontmatter validation passed; browser testing verified evidence expansion, demo Accept/Decline/Later, reset, disabled acceptance without evidence and exported decision JSON. Preview saved in ui/preview.png. These are prototype checks, not production backend tests.


Version 1.1 adds executable SQLite before/after query tests: correct repo/profile/exposure/window eligibility, missing-value counts, signed payload/time changes, negative regressions, zero baselines, empty cohorts, duplicate-event constraints and saved query hash. The small synthetic sample is deliberately inconclusive despite an 80% payload reduction and 10% slower tool duration.

Browser checks for v1.1 passed: accepted and rejected decisions remain in history, acceptance leaves implementation not started, the saved query can be expanded, and decisions persist across reload. The historical comparison row is explicitly synthetic and inconclusive.
