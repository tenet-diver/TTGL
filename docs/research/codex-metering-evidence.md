# Codex subscription-backed metering: official evidence

Reviewed 26 October 2026. Official source is pinned at
[`openai/codex@970111f6`](https://github.com/openai/codex/tree/970111f6cb62cc02fe36a82ea7d71b37a2889c97).
The installed CLI identifies itself as `0.163.0`. Source hashes, failed fetches,
line references and installed-schema checks are in
[codex-metering-sources.json](codex-metering-sources.json).

## Finding

**Yes: Codex can expose token usage while using a ChatGPT subscription. A
separately billed API account is not a prerequisite for token metering.** The
official README recommends signing in with ChatGPT for Plus, Pro, Business, Edu
or Enterprise access, and describes API-key authentication separately.

The earlier pilot's lack of telemetry was a limitation of the interface and
execution path used for that pilot. It must not be generalized into “Codex
subscriptions cannot be metered.” Its archived unknown values should remain
unknown unless corresponding, attributable usage records can actually be
recovered.

The official CLI/SDK is already an appropriate existing harness. The TypeScript
SDK wraps Codex, supports continued threads and exposes structured usage events.
It can inherit the existing authenticated environment; supplying an API-key
override is optional. There is no need to build an alternative coding loop just
to obtain token counters.

## Four useful observation surfaces

| Surface | What the inspected implementation exposes | Important limit |
|---|---|---|
| `codex exec --json` and TypeScript SDK | `turn.completed.usage`: input, cached input, cache-write input, output, reasoning output | Current source copies a cumulative thread snapshot, despite a per-turn SDK comment |
| App-server `thread/tokenUsage/updated` | Thread and turn IDs, `total` and `last` usage snapshots | Updates may replay on attachment; they are not all new spending |
| Durable rollout `TokenUsageRecord` | Per-response usage, response/thread/turn/session/root-turn IDs, cumulative turn and thread usage | Best-effort provider observations; absent usage stays incomplete |
| App-server `account/usage/read` with `threadId` | Backend estimated credits and nullable estimated USD, plus token groups by model, reasoning effort and speed | Requires the account's billing route; backend 403/404 produces no thread estimate |

Official entry points:

- [Subscription authentication](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/README.md#using-codex-with-your-chatgpt-plan).
- [SDK streaming usage example](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/sdk/typescript/README.md#streaming-responses).
- [SDK usage fields](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/sdk/typescript/src/events.ts#L20-L38).
- [App-server request method](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/codex-rs/app-server-protocol/src/protocol/common.rs#L1372-L1376).
- [Thread estimate and per-model groups](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/codex-rs/app-server/src/request_processors/account_processor.rs#L1259-L1337).

After normal app-server initialization and account authentication, the supported
request shape is:

```json
{"id": 1, "method": "account/usage/read", "params": {"threadId": "the-thread-id"}}
```

The exact method is `account/usage/read`, not `account/tokenUsage/read`. The
response's optional `threadUsage` includes `estimatedUsageCreditsMicros`, nullable
`estimatedUsageUsdMicros`, and `groups`. A group carries model, reasoning effort,
speed, estimated credits, net-new input, cached input, input, output and total
tokens. The inspected server explicitly requires ChatGPT/Codex-backend account
authentication for this route. Its presence does not establish entitlement for
every account or retroactive availability for every old thread.

This is supported by the installed binary, not only a source checkout:

```bash
codex app-server generate-ts \
  --out /tmp/codex-metering-installed-schema --experimental
```

That command succeeded without a model call. Its generated `ClientRequest.ts`,
`ServerNotification.ts` and `v2/ThreadUsage.ts` contain the methods and fields
above. This proves schema support in the installed CLI. It does not prove that
an authenticated live request succeeds in the present managed environment.

## Avoid double counting resumed conversations

The current SDK comment describes usage as “during a turn,” but the inspected
CLI implementation stores `ThreadTokenUsageUpdated` and constructs the
completion's usage from `usage.total`. Therefore an aggregator must not assume
that each completed resumed invocation is an incremental amount to add.

The official rollout test gives an explicit example: two responses consume
120 and 80 tokens in the first turn, yielding a cumulative thread total of 200.
After resume, another response consumes 30 tokens, yielding 230. Correct new
usage is 30, not 230; summing completion snapshots as 200 + 230 overcounts.
Restored token-count notifications can also be sent when a client attaches to an
existing thread. Replayed observations are not new inference.

The robust experiment ledger should prefer distinct provider response records,
deduplicated by their response identity and attributed to the correct task and
thread. Alternatively, store start/end snapshots for each known thread and use
validated deltas, retaining resets, missing observations and partial failures.
Collect controller, router and expert threads independently. The inspected
backend's estimated parent-thread bill does not document whether it includes
child-agent work; do not sum parent and child estimates without establishing
that accounting boundary.

The source also defaults missing CLI usage notifications to an all-zero `Usage`.
That is a serialization behavior, not proof that no inference occurred. A
completion with zero counters needs a completeness check against underlying
notifications or response records. A failed task can still have incurred usage,
so accounting should not depend only on successful final-turn events.

## Token categories are not all additive

Cached tokens are a component of input. Reasoning tokens are a detail of output.
The official response-parsing test uses input 100, cached input 40, cache writes
60, output 10 and reasoning output 5, while total tokens are 110. Adding every
displayed counter would incorrectly produce 215. Preserve all categories, but
apply only the provider's actual counting and pricing rules. Model reroutes and
reasoning-effort changes should be attributed to the actual serving model when
available, not only to the originally requested alias.

## What this permits us to claim

Subscription-backed runs can support measured token efficiency, expensive-model
usage, and task success at a specified resource allocation. With the backend
estimate route available, they may also support comparisons of **provider-estimated
credits or dollars**, labelled exactly that way. Applying public API prices to
observed tokens provides a separately labelled API-equivalent cost scenario.

Neither calculation is automatically an observed reduction in the subscriber's
cash bill. A fixed monthly subscription has an allocation, rate limits and
opportunity cost; fewer tokens do not necessarily lower that month's charge.
Useful subscription endpoints include successful tasks per quota window and an
explicit allocation of the subscription fee over productive tasks. API-equivalent
cost, backend estimated usage cost, subscription cash expense and full deployment
cost should remain separate reported quantities.

No paid inference, new model trial or account-usage request was performed for
this source review. It establishes the available mechanisms and the necessary
accounting corrections. Runtime access and live completeness still require a
small authenticated validation with fresh and resumed controller/expert threads.
