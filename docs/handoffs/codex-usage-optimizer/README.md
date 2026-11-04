# Codex Usage Optimizer — implementation and agent pack
Version 1.1 · 4 November 2026

A focused first product: import existing usage/activity logs, observe ordinary coding sessions, discover expensive patterns, and present evidence-backed changes for **Accept / Decline / Later**. Accepted changes run as bounded experiments and can be rolled back. The earlier memory/context research handoff remains a later extension; this product does not depend on Qdrant or a memory system.

Included:

- IMPLEMENTATION_GUIDE.md — architecture, data, UI, estimates, experiments and backlog.
- OPTIMIZATION_CATALOG.md — 100 distinct optimization hypotheses.
- skill/codex-usage-optimizer/ — reusable optimizer skill, on-demand recipe lookup and reference detector.
- schemas/ and examples/ — contracts and explicitly synthetic fixtures.
- ui/review.html — self-contained interactive review prototype; buttons record local demo decisions only.
- ACCEPTANCE_TESTS.md and SOURCES.md — validation requirements and checked integration sources.

This is a coding-agent-ready guide plus a usable skill/reference-analysis pack, not a deployed monitoring product. No historical private logs have been imported and no Codex/global settings have been changed. The fixture analyzer implements one narrowly scoped detector (large passing-test output), not all 100 techniques.

The skill is packaged here for handoff, not installed globally. Its paths are self-contained. Read SKILL.md and use scripts/recipe_lookup.py to load only matching recipe details. Python helpers use the standard library. Package schema validation additionally uses jsonschema/referencing.

Start implementation with ccusage for session usage and a raw-rollout/AI Observer adapter for tool detail. Never pretend aggregate usage reveals which individual tool produced the overhead. APIs and log formats must be version-pinned and tested on fixtures before live import.


## Version 1.1: optimization history

OPTIMIZATION_HISTORY.md adds persistent accepted/rejected decisions, verified implementation tracking, per-tool technique history and saved before/after queries. examples/before-after.sql is executable against the supplied synthetic SQLite fixture. The UI prototype includes a demo history and query preview; it still makes no real settings changes. Results separate payload reduction from elapsed time, quality and billing.
