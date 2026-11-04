# Codex context experiment handoff

Read EXPERIMENT_DESCRIPTION.md first, then CHECKLIST.md. This package is a
specification and templates only; it contains no executable harness or live results.

Start with M0: reuse existing observability, verify integration capabilities and
identify gap-only changes. The proposed `ctxexp` commands must be implemented;
they are not existing Codex commands. Do not run paid trials from these templates.

Files:
- EXPERIMENT_DESCRIPTION.md — complete design, ten ideas, protocol and references.
- CHECKLIST.md — milestone and acceptance checklist.
- configs/experiment.yaml — all ten independent toggles, default disabled/shadow.
- configs/variants.yaml — selected declarative overrides.
- tasks/tasks.yaml — real-task manifest template; REQUIRED placeholders block runs.
- audit/ — observability map and capability inventory templates, not audit findings.
- ANALYSIS_PLAN.template.md — preregistration checklist.
- prompts/CODING_AGENT_HANDOFF.md — reusable implementation/execution prompts.
- MANIFEST.sha256 — package integrity hashes (excluding itself).

No source repositories, credentials, existing telemetry or original attachments
are bundled. The main document records the unavailable source attachments.
