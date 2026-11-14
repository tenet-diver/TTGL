# Activity suggestions and task evidence

The Observatory's **Suggestions** page uses the configured small model to analyze
collected activity into proposed tasks, typed/tagged subtasks and up to five
improvement suggestions. This extends the earlier session-ID discovery: recorded
session boundaries remain provisional; the model can propose meaningful task
boundaries across turns. It does not silently replace explicit assignments.

## Review workflow

1. Open Suggestions and select a project or all recorded projects. Choose a recent
   or older activity window. Each finite review covers up to 20 recorded turns and
   400 tool steps. Large windows fail with a scope instruction; they are not
   silently sampled or presented as complete. Existing individual task mining
   remains available for larger tasks within its own limits.
2. Click **Analyze recent activity**. The existing configured Codex small model
   (`gpt-6-luna` by default) or local Ollama-compatible route receives a frozen,
   bounded source snapshot, including up to 40 attributed evidence reports from the selected tasks (2,000 detail characters each). These reports supplement native evidence and are not independent verification. Adding a report changes the review fingerprint. Prompts are sanitized, and source text is treated as
   untrusted evidence. No scheduled inference is created. Identical completed
   snapshots reuse their result; active attempts deduplicate. Failures and model
   usage are retained, including consumed inference on rejected output.
3. Inspect proposed tasks, subtasks, activity types, tags and confidence. Validation
   requires each selected turn to occur exactly once, and every selected source
   step to occur exactly once within its proposed task. Different repositories
   cannot be merged into one task. Suggestions must cite selected source steps
   and include an action, risk/uncertainty and a validation plan. No improvement
   percentage or successful outcome is inferred from a suggestion.
4. **Accept task grouping** atomically creates a task and interpreted subtasks,
   assigns the exact source turns and indexes the interpretation for search.
   Only unassigned turns or untouched provisional discovered tasks can move.
   Explicit assignments, confirmed/completed task states and user-curated step
   groups are protected. A changed source refuses acceptance. Acceptance is
   idempotent; source tasks and prior interpretations are retained. The new task
   stays **unresolved**, with no invented acceptance evidence.
5. Review improvements using **Accept for trial**, **Later** or **Decline**. These
   persist decisions; they do not apply code, run trials, change routing or claim
   savings. Source references open the existing bounded retained-evidence reader.

The activity-analysis cost is a shared review overhead, shown on Suggestions.
Accepted task interpretations reference that review; its token total is not
copied into each derived task as if it were separate inference. Missing usage
remains unknown. Source task counters and recorded outcomes are unchanged.

## Per-task evidence

Open a task in Work, then **Evidence & outcomes**:

- **What changed:** retained native FileChange patches/status, a bounded diff
  excerpt and its hash, original step reference and source line. Failed or
  unverified patch attempts are distinguished from reported successful changes.
  The current working tree is never substituted for historical evidence.
- **Screenshots and visual references:** retained native image-view references,
  image paths mentioned in operation output and explicit supplied URLs. References
  are not proof of a before/after comparison or visual correctness. Referenced
  files are never read, and URLs are never fetched, automatically. There is no
  claim that historical screenshots can be recreated after the fact.
- **Validation:** candidate validation operations display their retained command,
  bounded result excerpt, exit code and command-passed/command-failed/unknown
  status. Command success alone does not establish adequate coverage or whole-task
  acceptance. Task outcome and the recorded validation evidence are separate.
- **Your intervention:** explicit user/agent intervention records are attributed
  as reports, not independent verification. Recorded follow-up user messages are
  shown separately. A follow-up, approval, clarification or new request is not
  automatically counted as interference or failure.

A form adds a change note, screenshot/PR/validation URL, validation result or
confirmed intervention. URLs must be HTTP(S) without embedded credentials;
file/javascript URLs are refused. All model/source content is escaped in the UI.
Notes do not mark a task completed. The view includes coverage, missing-evidence
messages and truncation markers rather than treating missing proof as a pass or
assuming no human intervention occurred.

Source scanning is bounded to 50,000 retained records and 120 native evidence
facts; per-patch/command excerpts have explicit limits. Authorized source files
are reused; log-suggested file paths are never opened. Missing originals and
unsupported native shapes remain coverage gaps. Add a retained reference or an
explicit note rather than fabricating screenshots, changes or test outcomes.

## Agent access

The existing stdio MCP is version 1.3.0, with:

- `analyze_recent_activity`: one finite review; optional project and source-history
  `window_offset` (0, 20, 40, …). This invokes inference explicitly.
- `query_activity_suggestions`: compact attempt/usage summary by default. Request
  `section=suggestions` or `section=tasks` with bounded record pagination. Source
  window offsets are independent of record-page offsets.
- `accept_activity_task`: explicit, validated acceptance of one proposed boundary.
- `review_activity_suggestion`: decision only; no implementation or measured result.
- `get_task_evidence`: coverage/gap/count summary by default; select a kind and
  bounded page for evidence records. Details are limited to 1,200 characters;
  `read_evidence` retrieves retained original steps progressively.
- `record_task_evidence`: explicit attributed evidence note/reference.

Existing history search and task/subtask/source drill-down remain available.
No new database service, model runtime, package or external UI is installed.
The existing private SQLite task store gains additive tables and audit events;
PostgreSQL/ClickHouse telemetry schemas and historical study sources are unchanged.
The page uses the current shared Geist/shadcn-derived UI components and tokens.

## Verification and limits

Unit/API checks cover exact source coverage, invented IDs, stale acceptance,
idempotency, explicit/confirmed task protection, decision-only behavior, retained
usage on invalid model results, older windows, native changes and validation,
unsafe reference URLs, and follow-ups not being asserted as interventions.

The opt-in Chromium flow exercises the Suggestions button through a clearly
labeled model fixture, task/subtask acceptance, native change and screenshot
references, validation status, explicit intervention recording, saved decisions
and a 390px mobile evidence dialog. It reports no page errors. This is integration
verification, not a claim of live model quality or measured workflow improvement.

```sh
python3 -m unittest discover -s tools/usage-monitor/observability -p test_activity_insights.py
python3 -m unittest discover -s tools/usage-monitor/observability -p test_task_evidence.py
TTGL_BROWSER_QA=1 python3 -m unittest discover -s tools/usage-monitor/observability -p test_activity_insights_browser.py
```

Actual analysis needs collected source activity and a reachable configured model.
This cloud checkout does not import other machines' private histories through Git.
Its native provider network restrictions have not been bypassed. Existing paused
research schedules remain paused; this feature adds user-requested finite reviews.
