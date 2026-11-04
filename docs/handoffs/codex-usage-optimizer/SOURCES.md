# Checked source boundaries
Checked 4 November 2026. Integration capabilities must be rechecked against the installed version. Recipe-specific command flags are intentionally not hard-coded; verify help and repository policy before proposing a change.

- [ccusage Codex source](https://ccusage.com/guide/codex/): reads Codex local logs and produces usage reports; support is marked experimental. Treat aggregate data separately from tool profiling.
- [AI Observer import documentation](https://github.com/tobilg/ai-observer/blob/main/docs/import.md): historical import and source-path controls. Import coverage and historical reconstructions must be validated, not assumed equivalent to live telemetry.
- [AI Observer](https://github.com/tobilg/ai-observer): local monitoring/import/watch and portable export options; avoid overlapping ingestion paths.
- [Langfuse Codex plugin](https://github.com/langfuse/codex-observability-plugin): transcript-based collection, version requirements and full tool-content capture; configure local destination explicitly.
- [Langfuse CLI](https://langfuse.com/docs/api-and-data-platform/features/cli): programmatic access to traces/observations/metrics through its API-backed CLI. Discover actual endpoint commands before use.
- [Codex hooks](https://learn.chatgpt.com/docs/hooks): tool/request lifecycle instrumentation and its limitations. Diagnostic model hooks are not arbitrary prompt middleware.
- [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference): version-dependent settings, MCP tool exposure and schema controls. Eager/deferred exposure affects whether disabling a server saves context.
- [pytest output](https://docs.pytest.org/en/stable/how-to/output.html), [Vitest reporters](https://vitest.dev/guide/reporters), [Jest CLI](https://jestjs.io/docs/cli): reporting, verbosity/capture and runner controls differ by tool/version; quiet mode must preserve useful failures.
- [ripgrep guide](https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md): scoped searching, filters and output modes provide candidate mechanisms; confirm intended search completeness.
- [git diff](https://git-scm.com/docs/git-diff): summary/path-scoped patch inspection is useful for discovery; does not replace final review.

Recipes whose source_status is requires_tool_specific_verification are engineering hypotheses with no claimed universal option or measured savings. Generic architecture, estimate rules and UI contracts are newly proposed design choices. No empirical optimization percentages are supplied by this catalogue.
