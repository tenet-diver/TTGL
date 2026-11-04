# 100 evidence-driven optimization recipes

These are candidate hypotheses, not 100 changes to enable. No recipe has a default numerical savings claim. Tool options must be checked against the installed version. Recipe categories are navigation tags, not automatic authorization.

## Output

### OPT-001 — Concise successful-test reporter

Evidence trigger: Passing test logs dominate model-visible output.

Change: Use a supported compact reporter while retaining failures and exit status.

Check: Compare passing and deliberately failing fixtures. Risk: May hide diagnostic context.

### OPT-002 — Capture noisy subprocess stdout

Evidence trigger: Application prints swamp otherwise useful test results.

Change: Capture stdout and show it on failure instead of streaming every print.

Check: Inject a failing assertion and confirm captured output is accessible. Risk: Some tests depend on terminal behavior.

### OPT-003 — Reduce routine runtime log level

Evidence trigger: INFO or DEBUG repeats on successful runs.

Change: Set the task-local log level to warning or equivalent when debugging detail is unnecessary.

Check: Confirm warnings and errors survive; compare a debug-needed task. Risk: Root cause clues may need debug logs.

### OPT-004 — Suppress terminal progress redraws

Evidence trigger: Progress bars or carriage-return updates inflate output.

Change: Select noninteractive progress-free output for agent commands.

Check: Compare final result and failures against original. Risk: Some progress contains useful status.

### OPT-005 — Remove ANSI and terminal control noise

Evidence trigger: Captured output contains escape sequences or screen rewrites.

Change: Use supported plain-text/no-color output.

Check: Compare readable messages and byte/token counts. Risk: Text normalization may alter snapshots.

### OPT-006 — Deduplicate repeated warnings

Evidence trigger: Identical warnings recur many times in one run.

Change: Show each warning signature with count and first/last location; archive originals.

Check: Verify unique warnings and counts remain recoverable. Risk: Different warnings may share text.

### OPT-007 — Bound successful build chatter

Evidence trigger: Successful build steps print routine command banners.

Change: Use the build tool's verified quiet/summary option.

Check: Compare artifacts and a failing-build diagnostic fixture. Risk: Global quiet mode may suppress errors.

### OPT-008 — Present large logs as structured excerpts

Evidence trigger: A few failures are buried in large logs.

Change: Show exit status, failing sections and original-log reference.

Check: Verify protected diagnostics and exact original retrieval. Risk: Parser may omit an unfamiliar error.

### OPT-009 — Keep structured output instead of duplicate formats

Evidence trigger: The same operation prints JSON plus a human report.

Change: Return only the format needed by the agent; retain other artifacts on disk.

Check: Compare fields needed for task decisions. Risk: The selected format may omit interpretation.

### OPT-010 — Archive verbose dependency installation logs

Evidence trigger: Install logs repeatedly dominate context.

Change: Keep completion/error summary and filesystem log; expand on failure.

Check: Exercise missing dependency and lifecycle-script failure. Risk: Installer scripts may emit important warnings.

## Tests

### OPT-011 — Run the relevant test target during iteration

Evidence trigger: Full suite is rerun after every small scoped edit.

Change: Use a justified focused test target during iteration and full required verification at the end.

Check: Final full checks pass on same patch. Risk: Target selection can miss interactions.

### OPT-012 — Run failed tests first

Evidence trigger: A known failing subset is preceded by many passing tests.

Change: Rerun recorded failures first before the required broader checks.

Check: Match failure identity and retain final verification. Risk: Failure cache can be stale.

### OPT-013 — Use test collection to select cases

Evidence trigger: Broad test guesses cause repeated unsuccessful runs.

Change: Inspect bounded test names/collection output once and select explicitly.

Check: Selected test exists and checks intended behavior. Risk: Names alone may not reveal coverage.

### OPT-014 — Disable watch mode in agent jobs

Evidence trigger: Test command stays resident waiting for edits.

Change: Use the runner's supported one-shot mode.

Check: Command exits with correct status and same relevant coverage. Risk: Interactive development may need watch mode.

### OPT-015 — Avoid repeated coverage instrumentation

Evidence trigger: Every exploratory test run generates expensive coverage.

Change: Keep coverage for declared verification runs; omit during narrow debugging.

Check: Required final coverage check still runs. Risk: Coverage-dependent bugs may behave differently.

### OPT-016 — Separate artifact-heavy tests from smoke checks

Evidence trigger: Screenshots/videos/reports are generated on every successful iteration.

Change: Produce heavy artifacts only under the declared failure/final-run policy.

Check: A failing browser test still yields required evidence. Risk: May lose useful passing-run evidence.

### OPT-017 — Reduce oversized assertion diffs

Evidence trigger: Huge object diffs obscure the mismatching fields.

Change: Use a focused assertion or reporter preserving key differences and original artifact.

Check: A planted nested mismatch remains diagnosable. Risk: An overly narrow assertion weakens the test.

### OPT-018 — Choose bounded test concurrency

Evidence trigger: Tests contend for memory and run slower in parallel.

Change: Tune worker count to measured dev-machine capacity.

Check: Compare wall time, memory and flakiness at fixed test set. Risk: Lower workers can also be slower.

### OPT-019 — Reuse safe test-service setup

Evidence trigger: Repeated service startup dominates short test runs.

Change: Reuse a task-isolated service with explicit state reset.

Check: State-leak and fresh-start control tests pass. Risk: Shared state can corrupt correctness.

### OPT-020 — Use early failure for exploratory runs

Evidence trigger: Long test suites continue after a known blocker.

Change: Use supported fail-fast for diagnosis; preserve complete final verification.

Check: Full required checks run before claiming completion. Risk: Later independent failures are hidden temporarily.

## Search

### OPT-021 — Restrict search to relevant roots

Evidence trigger: Repository-wide results mostly come from unrelated packages.

Change: Search likely package directories first and widen if needed.

Check: Known relevant fixture remains discoverable. Risk: Initial package assumption can be wrong.

### OPT-022 — Exclude generated and vendored trees

Evidence trigger: Most matches are build artifacts or dependencies.

Change: Use repository-aware excludes for generated paths.

Check: Required source matches remain and exclusions are explicit. Risk: Generated output may itself be the bug.

### OPT-023 — List matching filenames before contents

Evidence trigger: Only file discovery is needed but full matching lines are returned.

Change: Use filename-only search then inspect selected files.

Check: Chosen files contain the intended match. Risk: Names may not distinguish relevant occurrences.

### OPT-024 — Use a fixed-string query when appropriate

Evidence trigger: Literal symbols are treated as expensive broad regex patterns.

Change: Use verified fixed-string mode for literal queries.

Check: Compare literal match set on fixtures. Risk: Escapes may have been intended as regex.

### OPT-025 — Cap per-file search output with counts

Evidence trigger: One file contributes hundreds of repetitive matches.

Change: Return bounded examples plus omitted-match count and expansion path.

Check: Important matches outside the cap can be retrieved. Risk: Top matches may not represent all cases.

### OPT-026 — Reduce search context lines

Evidence trigger: Each match includes large overlapping code windows.

Change: Use smaller context and expand around selected matches.

Check: Retain enough syntax for interpretation. Risk: Local context may be insufficient.

### OPT-027 — Avoid minified and binary search noise

Evidence trigger: Search results contain minified bundles or unreadable data.

Change: Restrict initial searches to appropriate source types.

Check: A source-map/generated-code investigation can opt back in. Risk: Exclusions can hide needed assets.

### OPT-028 — Combine compatible search queries

Evidence trigger: Several independent searches reread the same tree.

Change: Batch bounded patterns with labeled results.

Check: Each pattern's match set is identifiable. Risk: Combined output may grow too large.

### OPT-029 — Cache search results by repository revision

Evidence trigger: Identical searches repeat with no relevant file changes.

Change: Reuse bounded results keyed by query and tree/file hashes.

Check: Editing a searched file invalidates the cache. Risk: Stale results can mislead.

### OPT-030 — Locate symbols before reading whole files

Evidence trigger: Definition lookup repeatedly reads broad files.

Change: Use supported symbol/AST lookup to choose exact ranges.

Check: Resolve overloads and generated definitions correctly. Risk: Index may lag behind edits.

## Mcp

### OPT-031 — Filter records at the source

Evidence trigger: MCP results return many rows the agent ignores.

Change: Use supported server-side filters before returning records.

Check: Compare selected rows against unfiltered control. Risk: Filter assumptions may exclude necessary rows.

### OPT-032 — Project only required fields

Evidence trigger: Large nested fields are fetched but unused.

Change: Request explicit necessary fields when the tool supports projection.

Check: Required identifiers and error fields remain. Risk: Later steps may need omitted fields.

### OPT-033 — Paginate large MCP responses

Evidence trigger: Tool returns an entire collection for a small lookup.

Change: Use bounded pages with total/continuation metadata.

Check: Navigation reaches later pages without lost records. Risk: Too-small pages increase round trips.

### OPT-034 — Prefer count or aggregate operations

Evidence trigger: Raw records are fetched only to calculate a total.

Change: Use a supported count/aggregate endpoint.

Check: Check aggregate against a bounded raw sample. Risk: Aggregation semantics may differ.

### OPT-035 — Defer rarely needed tool schemas

Evidence trigger: Rare tool definitions are eagerly loaded in prompts.

Change: Use supported deferred exposure for the relevant server/tool profile.

Check: Needed tools remain discoverable; compare rendered schema size. Risk: Discovery overhead can outweigh savings.

### OPT-036 — Narrow task-specific tool exposure

Evidence trigger: Large eager tool set is unused for a task family.

Change: Use a reversible project/task profile exposing needed tools.

Check: Representative tasks still have necessary capabilities. Risk: Unused historically does not mean unnecessary.

### OPT-037 — Simplify overly verbose tool descriptions

Evidence trigger: Long repeated descriptions add measured prompt overhead.

Change: Remove redundant prose while preserving schemas and constraints.

Check: Tool selection/argument correctness remains acceptable. Risk: Shorter descriptions can worsen tool use.

### OPT-038 — Offer a task-specific batch read tool

Evidence trigger: Repeated small related MCP reads incur overhead.

Change: Use an available bounded batch operation with per-item outcomes.

Check: Match individual responses and partial failures. Risk: Batch tool can enlarge a single payload.

### OPT-039 — Cache immutable MCP resources

Evidence trigger: Same stable resource is repeatedly downloaded.

Change: Cache by resource identity/version and freshness policy.

Check: Updated resource invalidates or bypasses cache. Risk: Incorrect freshness harms results.

### OPT-040 — Avoid fetching attachment bodies prematurely

Evidence trigger: MCP listings eagerly include large attachments.

Change: Return metadata and explicit fetch references first.

Check: Needed attachments remain accessible under same permissions. Risk: Extra retrieval may add latency.

## Files

### OPT-041 — Read line ranges instead of whole files

Evidence trigger: Only a local region is needed in repeatedly large reads.

Change: Read bounded relevant ranges and expand on demand.

Check: Preserve enclosing definitions and constraints. Risk: Cross-file dependencies may matter.

### OPT-042 — Preview size before reading large artifacts

Evidence trigger: Unexpectedly huge file consumes a tool response.

Change: Inspect type/size and choose a bounded read strategy.

Check: Binary and text artifacts are classified correctly. Risk: Size alone does not indicate relevance.

### OPT-043 — Use change summaries before full diffs

Evidence trigger: Agent prints the full patch merely to discover changed paths.

Change: Inspect names/statistics first, then selected hunks.

Check: Final review still covers required changes. Risk: A summary is not a full review.

### OPT-044 — Scope diffs to the current task

Evidence trigger: Unrelated changes inflate patch inspection.

Change: Select task paths/base revision explicitly.

Check: Unrelated user changes remain preserved. Risk: Incorrect base hides relevant edits.

### OPT-045 — Avoid redisplaying already reviewed unchanged code

Evidence trigger: Same content hash is repeatedly sent to the model.

Change: Reuse an evidence reference and fetch only if needed.

Check: File changes invalidate the reference. Risk: Agent may need content back after compaction.

### OPT-046 — Extract configuration keys selectively

Evidence trigger: Whole config file is read for one setting.

Change: Use a parser to return exact key values and source paths.

Check: Missing/duplicate/overridden values handled correctly. Risk: Parsing may differ from actual tool precedence.

### OPT-047 — Read structured documents by sections

Evidence trigger: Whole large documentation page is fetched for one topic.

Change: Retrieve headings/selected section with original references.

Check: Cross-section prerequisites remain accessible. Risk: Section extraction can omit caveats.

### OPT-048 — Avoid lockfile and generated-file dumps

Evidence trigger: Large generated files dominate exploration.

Change: Inspect dependency metadata or targeted entries first.

Check: Actual lock resolution remains authoritative. Risk: Generated files can contain the relevant defect.

### OPT-049 — Return exact diagnostic slices from artifacts

Evidence trigger: Large compiler/report files are read wholesale.

Change: Parse needed errors/metrics with source ranges.

Check: A planted uncommon diagnostic is preserved. Risk: Parser may be tool-version dependent.

### OPT-050 — Deduplicate identical file content across worktrees

Evidence trigger: Same blob is read from many equivalent snapshots.

Change: Cache by content hash with scope-safe references.

Check: Different versions/permissions never collide. Risk: Path identity alone is insufficient.

## Context

### OPT-051 — Remove duplicated task instructions

Evidence trigger: The same instructions appear in several injected layers.

Change: Consolidate redundant text without changing priority or constraints.

Check: Effective requirements remain identical. Risk: Subtle instruction precedence can change.

### OPT-052 — Make project guidance relevant by directory

Evidence trigger: Every task loads extensive unrelated project guidance.

Change: Use supported scoped instructions for relevant subtrees.

Check: Applicable constraints remain loaded at the right paths. Risk: Scope boundaries can omit critical rules.

### OPT-053 — Use progressive disclosure for optimizer recipes

Evidence trigger: All 100 recipes are injected into every analysis.

Change: Load a compact index and only evidence-matched recipe details.

Check: Relevant recipes remain discoverable. Risk: Poor retrieval can miss a useful technique.

### OPT-054 — Replace stale working narrative with evidence-backed state

Evidence trigger: Repeated status prose grows while goals are stable.

Change: Maintain a bounded objective/constraints/progress summary with sources.

Check: Recover exact constraints and unresolved failures. Risk: Summarization can lose detail.

### OPT-055 — Preserve stable prompt prefixes

Evidence trigger: Volatile IDs/timestamps rewrite reused prompt prefixes.

Change: Move genuinely dynamic metadata after stable instructions where controllable.

Check: Measure cached input and task behavior. Risk: Prefix changes may not be fully controllable.

### OPT-056 — Compact only when useful and supported

Evidence trigger: Frequent compaction costs exceed observed benefit.

Change: Tune supported compaction boundaries using measured context pressure.

Check: No overflow or loss of task constraints. Risk: Delaying compaction can cause overflow.

### OPT-057 — Use exact archived references for older large observations

Evidence trigger: Old tool outputs stay large but are rarely revisited.

Change: In a verified context-control adapter replace eligible bodies with retrieval refs.

Check: Protocol closure, detail recovery and task success preserved. Risk: Stock Codex may not expose this control.

### OPT-058 — Avoid repeated verbose progress messages

Evidence trigger: Frequent narration is long and rarely used by the user.

Change: Use concise milestone updates while retaining actionable changes.

Check: User still receives useful progress/requests. Risk: Too little communication hurts collaboration.

### OPT-059 — Separate independent tasks into fresh sessions

Evidence trigger: Unrelated prior task history burdens new requests.

Change: Start an independent session with explicit minimal handoff.

Check: Necessary shared decisions are carried forward. Risk: Unnecessary resets cause rediscovery.

### OPT-060 — Bound subagent handoff and result content

Evidence trigger: Delegated tasks return entire transcripts.

Change: Return findings, paths and evidence references instead of full logs.

Check: Parent can expand evidence and verify results. Risk: Compressed results may hide important uncertainty.

## Repetition

### OPT-061 — Reuse unchanged verification evidence

Evidence trigger: Same checks rerun after no relevant changes.

Change: Reuse checks only when input/environment hashes match.

Check: Relevant change invalidates prior evidence. Risk: Insufficient dependency tracking creates false confidence.

### OPT-062 — Stop identical failure loops

Evidence trigger: Same command fails repeatedly with identical cause.

Change: Detect repeated error signature and change diagnostic strategy.

Check: Next action addresses new evidence instead of blind retry. Risk: Transient failures may legitimately need retry.

### OPT-063 — Bound polling frequency

Evidence trigger: Many status checks return no change.

Change: Use adaptive intervals or completion notifications.

Check: Completion/failure detection remains within acceptable delay. Risk: Long intervals slow reaction.

### OPT-064 — Avoid duplicate dependency installation

Evidence trigger: Install command repeats with unchanged lock/environment.

Change: Reuse verified task-isolated installation keyed by lock/toolchain.

Check: Changed lock and missing dependency trigger installation. Risk: Cache corruption can conceal differences.

### OPT-065 — Batch independent read-only tool calls

Evidence trigger: Independent reads are executed serially.

Change: Run bounded concurrent reads with labeled results.

Check: Respect rate limits and consistent snapshot. Risk: Parallel outputs may race with edits.

### OPT-066 — Avoid parallelizing memory-heavy tools

Evidence trigger: Concurrent tests/builds cause swapping and longer runtime.

Change: Serialize or lower concurrency for measured resource-heavy steps.

Check: Compare critical-path time and peak memory. Risk: Serialization can increase latency on capable machines.

### OPT-067 — Debounce verification during rapid edits

Evidence trigger: Checks run after every tiny edit burst.

Change: Run after a coherent change boundary or debounce window.

Check: Required final checks still complete. Risk: Long debounce delays defect discovery.

### OPT-068 — Reuse prepared repository indexes

Evidence trigger: Every session rebuilds the same read-only index.

Change: Reuse a versioned index with explicit invalidation.

Check: Edits and branch changes invalidate affected entries. Risk: Stale symbol data can mislead.

### OPT-069 — Prefer event-driven job completion

Evidence trigger: Agent repeatedly reads logs to learn whether a job ended.

Change: Use supported completion/status events and one final log fetch.

Check: Lost-event fallback and failures handled. Risk: Completion events may be unreliable.

### OPT-070 — Avoid redundant agent delegation

Evidence trigger: Several agents explore the same files without distinct questions.

Change: Assign distinct scopes or reuse one evidence summary.

Check: Coverage of required investigation preserved. Risk: Overpartitioning misses shared dependencies.

## Execution

### OPT-071 — Use incremental builds with valid cache keys

Evidence trigger: Full rebuilds dominate repeated local iterations.

Change: Enable supported incremental artifacts keyed by source/toolchain.

Check: Clean-build verification confirms identical result. Risk: Incorrect cache invalidation causes stale binaries.

### OPT-072 — Skip unnecessary package-manager network checks

Evidence trigger: Repeated install/start commands spend time checking registries.

Change: Use supported offline/prepared-cache mode when dependencies are complete.

Check: Missing package fails explicitly; no stale resolution claim. Risk: Offline mode cannot fetch new dependencies.

### OPT-073 — Use a narrow lint target while iterating

Evidence trigger: Full repository lint repeats for one changed module.

Change: Lint relevant files early and run required full lint at completion.

Check: Full final check remains mandatory when specified. Risk: Cross-file rules may need broader analysis.

### OPT-074 — Avoid duplicate formatting passes

Evidence trigger: Multiple wrappers run the same formatter sequentially.

Change: Keep one equivalent formatting invocation per boundary.

Check: Final formatted content matches original pipeline. Risk: Wrappers may apply distinct options.

### OPT-075 — Reuse compiled test binaries safely

Evidence trigger: Tests recompile unchanged code every run.

Change: Use supported build/test cache with explicit toolchain/input keys.

Check: Clean control and changed-source invalidation pass. Risk: Cache state may alter behavior.

### OPT-076 — Reduce unnecessary service readiness waits

Evidence trigger: Fixed sleeps exceed actual startup time.

Change: Use bounded readiness probes instead of fixed delays.

Check: Probe captures real readiness and timeout diagnostics. Risk: A shallow probe can return too early.

### OPT-077 — Right-size timeout budgets

Evidence trigger: Commands hang long after a deterministic failure.

Change: Set task-specific timeout with cancellation and preserved partial logs.

Check: Slow valid fixture still has adequate budget. Risk: Aggressive timeout creates false failures.

### OPT-078 — Preserve a warm local helper when beneficial

Evidence trigger: Repeated local model/helper cold loads dominate processing.

Change: Reuse one bounded resident helper across authorized jobs.

Check: Measure memory contention and warm/cold latency. Risk: Resident model can starve development tools.

### OPT-079 — Remove duplicate transpilation layers

Evidence trigger: Tests/build scripts run equivalent transforms twice.

Change: Use one supported transformation path.

Check: Artifacts, sourcemaps and tests remain correct. Risk: Transforms may have subtly different semantics.

### OPT-080 — Avoid unnecessary container/image rebuilds

Evidence trigger: Image rebuild occurs without Dockerfile/dependency changes.

Change: Reuse pinned prepared image keyed by build context.

Check: Relevant context change invalidates the image. Risk: Mutable image tags can conceal differences.

## Data

### OPT-081 — Select structured response fields before serialization

Evidence trigger: Large JSON includes fields unused by the task.

Change: Project fields at source or in a verified wrapper.

Check: Required data and error metadata remain. Risk: Wrapper may change tool semantics.

### OPT-082 — Return bounded table previews with totals

Evidence trigger: Large tables are dumped for initial exploration.

Change: Provide schema/counts/sample and explicit query/expansion route.

Check: Sampling bias and omitted rows are visible. Risk: Sample may not reveal rare important records.

### OPT-083 — Retrieve specific documentation sections

Evidence trigger: Browser fetch includes navigation and unrelated page content.

Change: Use semantic section extraction with URL/source references.

Check: Required caveats and version context preserved. Risk: Extractor may remove important page state.

### OPT-084 — Prefer DOM/text evidence when images are unnecessary

Evidence trigger: High-resolution screenshots are used for text-only questions.

Change: Use supported accessible text/DOM extraction where sufficient.

Check: Visual-only information is not needed for the decision. Risk: Layout/state may require a screenshot.

### OPT-085 — Crop screenshots to the relevant region

Evidence trigger: Large images show mostly unrelated interface area.

Change: Capture the relevant region at sufficient resolution.

Check: Controls, labels and state remain identifiable. Risk: Crop can omit context needed to act safely.

### OPT-086 — Avoid duplicate browser captures with unchanged state

Evidence trigger: Identical screenshots/snapshots repeat between no-op actions.

Change: Reuse state evidence until navigation/mutation/time-sensitive change.

Check: State-change detection invalidates correctly. Risk: Dynamic pages can change without an action.

### OPT-087 — Limit debug traces to relevant components

Evidence trigger: Verbose distributed traces include unrelated services.

Change: Query a bounded time/component/error scope first.

Check: Correlated upstream/downstream cause still accessible. Risk: Narrow scope can hide propagation.

### OPT-088 — Fetch referenced attachments on demand

Evidence trigger: Messages include all file bodies before relevance is known.

Change: List attachment IDs/types/sizes first; retrieve selected ones.

Check: Necessary documents remain reachable. Risk: Discovery adds a round trip.

### OPT-089 — Compress transport without confusing model savings

Evidence trigger: Network time is high for compressible tool payloads.

Change: Use supported transport compression and measure bytes/latency.

Check: Response semantics unchanged; model tokens reported separately. Risk: Network compression does not reduce model context by itself.

### OPT-090 — Choose an existing specialized tool over broad raw scraping

Evidence trigger: General scraping returns noisy data available via a narrow API.

Change: Use the authorized specialized endpoint with explicit fields.

Check: Match accuracy, permissions and task capability. Risk: New tool schemas or fees may outweigh benefits.

## Knowledge

### OPT-091 — Retrieve known project commands from verified evidence

Evidence trigger: Agent repeatedly rediscovers identical build/test commands.

Change: Keep a small version-aware project command reference.

Check: Commands validated after toolchain/config changes. Risk: Stale guidance can cause failures.

### OPT-092 — Keep task constraints in a bounded checklist

Evidence trigger: Agent requires repeated reminders of existing requirements.

Change: Maintain exact active constraints outside optional retrieval.

Check: Later scope changes supersede prior constraints correctly. Risk: Checklist itself adds context.

### OPT-093 — Retrieve prior failures only when applicable

Evidence trigger: Repeated debugging rediscovers a documented failure mode.

Change: Retrieve evidence-backed lesson matching repository/version/symptom.

Check: Inapplicable or outdated advice is rejected. Risk: Negative transfer can waste time.

### OPT-094 — Improve query formulation before increasing top-k

Evidence trigger: Memory results are irrelevant despite large returned batches.

Change: Include current objective/error/file context in retrieval query.

Check: Compare relevance and downstream success at fixed budget. Risk: Query may overfit to a wrong hypothesis.

### OPT-095 — Reduce redundant retrieved chunks

Evidence trigger: Top results repeat overlapping source content.

Change: Deduplicate or diversify with source/range tracking.

Check: Unique required evidence remains. Risk: Nearby chunks may contain necessary nuance.

### OPT-096 — Set retrieval budgets from observed usefulness

Evidence trigger: Many returned memories are never expanded or used.

Change: Test smaller top-k/token budgets with a broader-search fallback.

Check: Held-out task quality and recovery preserved. Risk: Observed non-use is not proof of uselessness.

### OPT-097 — Defer costly reflection on trivial tasks

Evidence trigger: Local synthesis overhead exceeds likely saved work.

Change: Use importance/size thresholds and background scheduling.

Check: Useful high-impact lessons still qualify. Risk: Deferred insight may matter sooner than expected.

### OPT-098 — Use deterministic extraction before an LLM summary

Evidence trigger: Regular log formats are summarized by a model each time.

Change: Parse known structures mechanically and reserve local LLM for unstructured synthesis.

Check: Critical detail retention and parser-version tests pass. Risk: Mechanical patterns can miss novel content.

### OPT-099 — Avoid optimizer observation feedback loops

Evidence trigger: Optimizer sessions dominate the data they analyze.

Change: Tag and separate optimizer activity and its overhead from target sessions.

Check: Totals reconcile without excluding actual target cost. Risk: Filtering can hide real overhead if reported poorly.

### OPT-100 — Prevent overlapping recommendations from double counting savings

Evidence trigger: Several proposals modify the same output/context region.

Change: Track overlap groups; test combinations before summing benefits.

Check: Combined measurement replaces additive forecasts. Risk: Conservative aggregation may understate useful interactions.
