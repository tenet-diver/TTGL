# Codex Cloud handoff — context usage experiments

5 November 2026. Repository: https://github.com/tenet-diver/TTGL, branch `work`.
Use this existing repository; do not create another repository or a Codespace.
Implementation commit: `1c79a75`; also read subsequent policy/handoff changes on
`work`. This handoff distinguishes completed evidence from plans and blockers.

## Setup instructions

Follow [Codex Cloud setup](context-compression-cloud-setup.md) before trials.
The initial command is `sh tools/usage-monitor/experiments/cloud_setup.sh`; it
only inspects existing capabilities and runs dependency-free tests. It does not
install anything or approve the blocked image.

## Objective

Find what consumes tokens, API-equivalent cost and time, then test improvements
without losing task quality. Sources include instructions/skills, files, tool and
MCP results, tool-call arguments, conversation history and model output. Prefer
existing OSS and Langfuse capabilities over building another UI.

Run a controlled comparison of baseline, Headroom compression on insertion, and
older-output masking with placeholders and retrieval references wherever active
context control is actually supported. Count cache disruption, all retrieval and
summarization/model calls, failures and elapsed task time. Do not optimize cache
hit rate or raw token reduction in isolation. Model, task and checks must match.

## Mandatory security policy

Read `AGENTS.md` and `docs/security/dependency-security-policy.md` before any
installation, upgrade or first execution of downloaded software. Resolve the
whole graph, check current advisories including base OS and unscored findings,
review publisher/supply-chain incidents and execution hooks, verify artifacts,
and save a dated receipt before installation. Any known finding or incomplete
required check blocks execution. No silent exception. This includes scanners,
one-shot package runners, plugins, images and framework auto-installs.

Headroom 0.42.0 declares LiteLLM as a required Python distribution dependency.
The resolver selected 1.103.10, not the 1.82.7/1.82.8 or 1.107.0 versions named
in the March/October 2026 compromise reports. Matching registry hashes and zero
OSV package findings were insufficient to establish safety. LiteLLM was then
removed and the standalone compressor smoke test worked without it.

The original 95 wheel artifacts matched PyPI digests and had no known package
advisories in that check. However, the broader existing OSV scanner found **85
distinct advisory IDs across 38 package entries** in the experimental image.
Some are unscored/unimportant matches; this is not 85 proven exploitable flaws.
Under the user's rule, the image is nevertheless **BLOCKED**. Docker Scout
required a login; the already-installed OSV scanner supplied the image report.
No further Headroom execution is allowed using that image. Containers are stopped.

The blocked image ID was
`sha256:29fc34185f21647687cc3aca721369b6e8fc17ff1918e6ab4648d40730f914f5`.
It is local only, not a published/pullable runtime. Its Python base was
`python@sha256:ae14d4ce8771606477a81446e7ef429edd6762305fc50c84507c1041fa8285d1`.
Do not use the default Cloud/Codespaces image as an implicitly approved substitute
for a newly installed experiment runtime. Inspect existing managed capabilities
first and review any additional software/image before using it.

## Code available in this branch

- `tools/usage-monitor/experiments/context_pilot.py`: fixed read-only synthetic
  MCP fixtures, offline Headroom SDK adapter, local official-endpoint forwarding
  and native Codex metering. Requires a fresh passing receipt for the exact
  immutable image before creating a model or container process. Uses
  `docker run --pull never`, no credentials/mounts/socket, no network, read-only
  filesystem, UID 65532, dropped capabilities and bounded resources.
- `publish_context_pilot.py`: publishes finalized journals, measured generations,
  completed-trial timing and correctness scores to local Langfuse. Incomplete
  calls have separate names and remain logged. Uses immutable delivery receipts.
- `test_security_gate.py`: four checks covering missing/incomplete reviews,
  findings, expiry and different artifacts. All pass. Existing Langfuse suite:
  21 checks pass. The launch gate was also tested against the blocked receipt;
  it refused before launching anything.
- `tools/usage-monitor/server.py`: existing refresher now uses
  `npx --no --offline ccusage@20.0.48 ...`, refusing automatic installation/fetches.
  Existing cached executable and report refresh were verified locally.

No package installations are required for the pure Python unit tests:

```sh
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_*.py'
python3 -m unittest discover -s tools/usage-monitor/langfuse -p 'test_*.py'
```

## Actual experimental evidence, not a completed three-arm study

The plan was two fixture formats, two repetitions, three conditions, five staged
questions per assignment. Setup failures and started/uncertain calls are retained
locally, not silently retried or counted as free. Earlier attempts encountered
wire compression, native programmatic filtering, and unavailable-tool issues.
Those are setup checks, not treatment outcomes.

A later controlled pilot explicitly requested full marked observations before
answering, rather than the filtering the normal Codex host can perform. It
completed **one inventory assignment per baseline/Headroom condition**:

Both completed assignments passed their five fixture checks. Detailed measured
token and cost counters stay in the private user handoff, not the public document.

The tested setting was the **SDK agent/lossless mode**, ML disabled, recent
protection explicitly zero and first-insertion output memoized. Local o200k_base
counts for its three observations were 17,950→17,950, 17,921→17,921 and
17,943→17,943. It produced **no compression** on these nested-JSON fixtures.
The small cost difference is not a causal/general result: n=1, model/runtime
variation and cache warm-up apply. This is not a test of every Headroom profile
or its stock cache-mode proxy. Detailed price scenarios remain in the private handoff. They are not
subscription cash charges or quota estimates.

The older-output masking arm failed its mechanism gate: the adapter did not
observe a successful older-result replacement. Investigate the actual native
request shape, context references/deltas and tool-host filtering before running
more inference. Do not assert that all Codex integrations forbid masking or report
zero savings for an intervention that never occurred. The full pilot stopped;
no complete comparison or quality-retention claim is available.

Live provider responses also contained an optional `usage.attribution.items`
field. It was retained locally but not mapped to input sources. Validate its
meaning and availability before claiming exact per-file/tool/cache attribution.

## Existing observability and data limitations

Langfuse is primary; the local companion remains available. These are **on the
user's Mac**, not reachable as Cloud `localhost`:

- Main: `http://localhost:3000/project/ttgl-codex/dashboards/cmw2k9kd90003p61tatyoxvn6`
- Partial pilot: `http://localhost:3000/project/ttgl-codex/dashboards/cmw2qpjv00021p61tjiug90t3`
- Companion: `http://127.0.0.1:8766`

The local import covers retained rollout logs, not all indexed chats or complete
vendor transcript replay. Detailed historical counts and source estimates stay
in the private user handoff. Input cache dominates the local historical usage,
but source attribution is a conditional reconstruction rather than verified
per-source billing/cache membership. Tool results, argument history and
instructions have substantial exposure, alongside explicit unknowns.

Do not infer individual costly files from generic cat/sed/instruction categories.
Read/exposure frequency alone is not cost; a once-read result can recur in many
later requests. Source fingerprints/drill-down remain a gap.

Timing uses explicit native item.duration; lifecycle windows can be grossly
inflated. Preserve all outcomes and show count/median/p95/p99/max, not outlier
filtering. Process durations overlap and are not task or agent-waiting time.

Measured daily/session/context projections are alternative views; never sum
them. Langfuse v4 observations are immutable: preserve outbox/receipt ledgers,
do not blindly resend span IDs or overwrite imported counters. The experiment
projection is separate; actual inference overhead also remains in normal native
usage. No raw transcripts or private runtime records are committed here.

## Cloud continuation

1. Read this branch's instructions, inspect capabilities and current journals
   available to Cloud, and do not assume Docker, Codex CLI or subscription proxy
   support. Do not copy Mac auth files or invent billing/usage from absent logs.
2. Find a supported minimal runtime that passes the full security gate, or
   record a concrete blocker. Do not bypass the strict policy to get a result.
3. Validate actual result exposure and mutation without scored inference first.
   Preserve opaque native reasoning/call IDs. Use supported context control.
4. Register a fresh bounded protocol and independent assignments before new model
   work. Do not silently resume/retry uncertain local assignments. Match model,
   effort, tasks, quality checks and whole-task accounting. Include all retrievals,
   compression overhead, cache misses, setup failures and unknown metering.
5. Prefer Langfuse for results if an approved connection exists. Otherwise keep
   private JSON/CSV in Cloud outputs for later local publication. No public ports,
   raw histories, credentials or broad repository-token scopes. TTGL is public;
   do not push private experiment journals. Do not build another trace UI.
6. Preserve frozen historical studies and keep the old research heartbeat paused.
   Do not resume unrelated Luna/Sol routing research.

Local raw journals/security reports are under the Mac workspace's
`work/headroom-experiment/` and user-facing `outputs/`; they are not available in
the public Git clone. This public document intentionally omits private measured-usage tables. It is
the sanitized checkpoint, not a substitute
for the missing raw records. Request only the minimum sanitized evidence if
required; never upload credentials or local history to reconstruct it.
