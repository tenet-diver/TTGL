# TTGL Usage Observatory

A working local Codex companion: retained session usage, daily/model/session views, tool evidence, recurring-opportunity rules, agent-authored reviews and durable review/decline/defer history. This is an initial monitor, not the complete handoff executor.

## Run

Requires Python 3.9+, Node/npm (`npx`) and the installed `zstd` executable. Token accounting reuses MIT-licensed ccusage **20.0.48** rather than duplicating its cumulative/fork/compaction logic. The version's help and live output were checked on 4 November 2026; no paid service is needed. `npx` installs the pinned release from the npm registry on first use; reports use `--offline --no-cost` and do not upload logs. No live pricing or billing estimate is calculated. The custom portion adds the review UI, local evidence rules and decision history that aggregate reports do not provide.

On macOS, `python3 tools/usage-monitor/manage.py install` copies the application into `~/Library/Application Support/TTGL Usage Monitor`, installs a user LaunchAgent with restart and login startup, and installs the `ttgl-usage-monitor` skill. Existing data is preserved. Open http://127.0.0.1:8766. Use `manage.py status` or `manage.py stop` to inspect/stop the service. Re-running install updates the installed app and starts it again.

For a foreground service: `python3 tools/usage-monitor/server.py --data /absolute/local/private/data --port 8766`. Source defaults to `~/.codex`; use `--codex-home` for another root. Source directories are read-only. SQLite stores normalized metadata, sizes, hashes and decisions, not raw commands/results. Runtime data, reports and agent reviews stay outside Git. The service is loopback-only; mutations require the same browser origin. No raw histories are sent to an LLM.

## What is implemented

- ccusage session/daily JSON snapshots every three minutes. Input here is uncached input; cached reads are separate. Reasoning is within output. Reports run sequentially while sources can change; coverage includes the observed daily/session reconciliation residual and capture times.
- Plain and zstd historical import, active/archive duplicate precedence, native completion-ID deduplication, replay-prefix exclusion by session timestamp/thread identity and legacy request/result matching. Native output sizes refer to retained serialized results, which may already be truncated, not exact provider-visible payloads. Native timestamps measure tool completion intervals, not whole-task elapsed time. Legacy timing/outcomes remain null.
- Changed-file polling every 20 seconds. Unchanged files are skipped. Changed files are re-parsed in full, so large active logs add overhead; this is not yet an offset-based low-overhead collector. Malformed/oversize lines and per-file errors are visible in coverage. Format support is based on observed local versions, not a universal stable OpenAI log schema.
- Up to five recurring-opportunity cards: large tool results and repeated identical retained output. The other handoff detectors remain unimplemented. These rules do not prove wasted work. Project and model filters apply to the session browser; tool findings currently cover the imported corpus.
- Explicitly labeled Codex-reviewed cards can be stored in `data/agent-reviews.json`. This chat authored the initial reviews against frozen evidence. Automatic rule findings refresh locally; there is no autonomous background LLM. The installed skill queries `/api/agent-context` for later Codex analysis.
- Review choices persist in SQLite and an append-only event log. They never apply a patch. Execution, bounded trials, adoption/rollback, result comparison UI and savings remain future work. Declines suppress overview resurfacing with stable IDs; all decisions remain inspectable.

## Verify

`python3 tools/usage-monitor/test_monitor.py` checks replay exclusion, duplicate completions, legacy joins, unknown fields and import idempotency. `node --check tools/usage-monitor/app.js` checks UI syntax. Actual UI overview, suggestion navigation and evidence dialogs were inspected with local history. The original handoff fixtures passed separately. Private runtime totals are intentionally not committed here.

Source evaluation: [ccusage Codex source documentation](https://github.com/ccusage/ccusage/blob/main/docs/guide/codex/index.md), [MIT license](https://github.com/ccusage/ccusage/blob/main/LICENSE), and [v20.0.48 release](https://github.com/ccusage/ccusage/releases/tag/v20.0.48). Codex interface review: [official developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli); local rollout field support was established from the selected local corpus.
