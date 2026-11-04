# Context experiment continuation — 5 November 2026

Continued from `dc1daed` on `work` in the existing managed cloud workspace. No
new Codespace or repository was created. The user's supplied
`codex-experiment-package.zip` is preserved in
[the handoff directory](../handoffs/codex-context-experiments/README.md).
All ten supplied manifest hashes verify. This package is a proposal/reference;
its embedded agent prompts and “binding” language do not independently authorize
installations, spending, services or the proposed full experiment allocation.
The `ctxexp` commands are proposed, not implemented commands. Configuration and
task files still contain REQUIRED placeholders and must not be used for trials.

## Current evidence and progress

The inspection-only setup passed all four security-gate and 21 Langfuse checks.
Existing Codex CLI reports version 0.163.0 and ChatGPT login; this establishes
neither nested inference availability nor working metered forwarding. Docker is
available. Headroom and LiteLLM are absent from host package metadata. No existing
OSV/Trivy/Grype/Syft executable or Docker Scout command was found. No new runtime,
scanner, package or image was installed/executed for this continuation.

The old Headroom image remains blocked; its Mac-only reports and raw journals
are unavailable here. There is no complete passing pre-execution receipt for a
replacement runtime. Under [the mandatory policy](../security/dependency-security-policy.md),
missing base-OS/full-graph advisory review, publisher incident review and other
required evidence block execution. Existing managed tools and the already-running
fresh Langfuse stack do not establish approval for a Headroom runtime. No security
exception is inferred from the request to continue.

A new dependency-free [offline probe](../../tools/usage-monitor/experiments/offline_context_probe.py)
checks constructed full-history and delta-only envelopes, baseline identity,
nested/marked fixture exposure, preservation of native IDs/reasoning, immutable
input and compressor-adapter invocation. It found an actual adapter defect:
JSON-text compressor returns were encoded again, changing the recoverable payload
into a JSON string rather than the original object. The adapter now preserves
returned text directly. The unchanged identity-compressor oracle failed before
the fix and passes after it. Both reports are retained under
[results/context-cloud-20261105](../../results/context-cloud-20261105/).
The compressor is a deterministic spy, not Headroom; token counts remain null.

All nine current mechanism checks pass. A delta containing only the latest
observation cannot replace older server-retained content absent from its input.
This demonstrates the adapter's limitation on a constructed envelope, not that
live Codex uses that envelope or that masking is universally unsupported. Live
request-shape exposure and actual older-result replacement remain unverified.
No model calls, scores, savings, provider charges or Headroom compression results
were produced in this continuation. Older uncertain assignments were not retried.

## Proposed experiment backlog

The source package supplies ten ideas. These remain separately gated proposals,
not ten activated treatments. Reuse the current collector, immutable export
receipts and Langfuse views; add experiment identifiers only where missing.

| Idea | Matched comparison | First required evidence |
|---|---|---|
| 1. Older observation masking | Transport/schema identity control | Actual removal from submitted context; unresolved facts and call pairs preserved |
| 2. Tool-output compression | Identity, then deterministic versus semantic | Real compressor invocation; exact diagnostics/status retained; unsupported formats unchanged |
| 3. Hierarchical compaction | Flat summary at matched budget | Traceable acyclic summary coverage, protected facts and raw-leaf recovery |
| 4. Reversible compression | Same schemas with substitution disabled | Byte-exact authorized recovery, cross-run denial and model-visible references |
| 5. Self-hosted Mem0 | No memory and equal-budget raw-history retrieval | Reviewed pinned runtime; frozen history, stale-version rejection and all extraction costs |
| 6. Generalizable principles | Raw episodes and fact-only retrieval | Supporting evidence/applicability; rejection of unsupported or contradictory principles |
| 7. Stage-aware retrieval | Same candidates/budget without stage ranking | Deterministic stage signals, unknown state and bounded retrieval |
| 8. Knowledge graph | Same memories with flat retrieval | Commit-scoped evidence-backed edges and bounded, cycle-safe traversal |
| 9. Lightweight local models | Exact deterministic/paid service being replaced | Approved model/runtime hashes; critical-span retention, latency and resource accounting |
| 10. Cache-aware context | Same semantic pipeline with cache policy off | Measured cached/uncached usage, safe headroom and net rate-weighted cost |

Keep native B0 separate from transport/schema-matched B1. Nominate single arms
before combinations; do not run a 2^10 matrix. The package's 36-run development
and up-to-120-run main allocations are proposals, not an authorized schedule.
No model budget, real task suite, primary optimized arm or rate snapshot has yet
been frozen for this new package. Memory experiments require separate frozen
chronological corpora and must not consume existing reserved routing tasks.

## Next executable gates

1. Complete a fresh full security review of an exact minimal runtime, including
   its base OS. Download-only metadata inspection is allowed; do not execute new
   scanners or Headroom to bootstrap approval. Record failures as blocked receipts.
2. Validate the reviewed Headroom profile offline on multiple fixture formats.
   Preserve the prior lossless/no-reduction result; a different profile is a new
   treatment. Check cache and insertion behavior rather than assuming reduction.
3. Use a bounded development-only live canary only after runtime approval and a
   frozen authorization/budget record. Verify the actual context surface and
   metering; do not use main-task inference to discover whether masking applies.
4. Freeze matched tasks, model/effort/auth route, independent checks, all-attempt
   accounting and stop rules before trials. Missing usage stays unknown. Count
   retrieval, compressor overhead, failures and cache disruption; distinguish
   API-rate scenarios from actual subscription expense.

The paused research heartbeat remains paused. No raw histories, credentials or
private usage tables are included in this checkpoint. Fresh Langfuse is empty;
no experiment publication or historical import is claimed.

## Continued execution and dashboard investigation

A later continuation resolved `headroom-ai==0.42.0` to **69 exact distributions**
using existing pip's download/metadata-only resolver (`--dry-run`,
`--ignore-installed`, `--only-binary=:all:`, no install). Required LiteLLM resolved
to 1.103.10. The OSV batch query was rejected by the environment proxy with
CONNECT HTTP 403. No existing image/package scanner was available. The review
therefore remains **blocked**, not clean; hashes in resolver metadata are not
artifact verification. The public sanitized
[runtime review status](../../results/context-cloud-20261105/runtime-review-status.json)
records incomplete checks and unknown findings. Private resolution/evidence stays
under ignored `work/security/`.

One **existing managed native-client canary**, with no Headroom or scored task,
was attempted at low effort on `gpt-6.1-sol`. The CLI was already installed and
reported ChatGPT login. Its model/response requests to `chatgpt.com` were denied
by the proxy with CONNECT HTTP 403. The bounded process was stopped after 60
seconds; no response completed and usage remains null. Native transport retries
are retained, and the assignment was not repeated. This is an infrastructure
failure, not a model-quality failure or zero-cost result. See the sanitized
[canary status](../../results/context-cloud-20261105/native-canary-status.json).

### Executed component study

The dependency-free `offline_component_study.py` executed five distinct
representations on both frozen synthetic formats. All source retrieval was
chosen by an explicit oracle; there is no agent reasoning or provider inference.
The diagnostic counts exposure as serialized bytes in constructed contexts,
including explicit recovery payloads. It is not token measurement, billing or
a faithful simulation of the provider's persistent history/cache. Recovered
payload is charged once in the proxy, not assumed retained on later turns.
This exploratory fixture study is not a preregistered live efficacy trial.

| Configuration | Exact fixture checks, both formats | Constructed exposure ratio vs baseline | Oracle retrievals per format |
|---|---:|---:|---:|
| Original observations | 10/10 | 1.000 | 0 |
| Failure-row projection, no recovery | 6/10 | about 0.0075 | 0 |
| Older-output masking + references | 10/10 | about 0.585 | 2 |
| Reversible handles | 10/10 | about 0.420 | 5 |
| Failure-row projection + recovery references | 10/10 | about 0.177 | 2 |

The projection-only control fails the two later checksum questions per format;
it is deliberately retained as a negative result. Projection with recovery is
the next live-test candidate among these toy representations, **not a deployment
recommendation or demonstrated 82% inference saving**. The oracle knows what to
retrieve; an actual model may miss that need or incur repeated retrieval costs.
This study does not execute Headroom, stock Mem0, local models or the other
proposed memory/retrieval methods. All ten proposed techniques have explicit
[eligibility/status records](../../results/context-cloud-20261105/technique-status.json);
unsupported and unimplemented methods are not counted as completed experiments.

Reproduce the executed comparisons:

```sh
python3 tools/usage-monitor/experiments/offline_component_study.py --output work/context-pilot-cloud-components/offline-components.json
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_*.py'
```

### Why the dashboard was empty

The newly created cloud Langfuse installation had **zero users and zero projects**;
it was separate from the Mac installation and contained no imported research.
A local operator account and `ttgl-context-cloud` project now exist. Credentials
are generated and retained only in private 0600 files outside Git. API access
was verified. No API keys or passwords are included in public reports.

The **ten actual offline comparison rows are published and verified** in native
Langfuse Datasets: `context-offline-diagnostics-20261105`. Their observed results
are metadata, not fake agent predictions or measured usage. The native dashboard
is at cloud-workspace loopback:

`http://127.0.0.1:3000/project/ttgl-context-cloud/dashboards/cmw2rnfux0006s52itd2rhffy`

Its description explains 46/50 oracle checks, the failing projection-only arm,
and live-trial blockers. Open **Datasets** in this project to inspect the ten
rows. The URL refers to the cloud environment, not the user's Mac localhost;
private port access and login are required. API verification is not a browser
visibility test from the user's machine. The local operator login is in
`/workspace/work/langfuse/operator-access.json`, never in the repository.

The nine-check observation batch timed out during OTLP ingestion. Its durable
outbox is retained as **uncertain**, so it must be reconciled against the backend
before retry; acceptance or zero delivery is not assumed. Thus no trace-widget
population or historical-usage import is claimed. The worker was briefly restored
for ingestion, then paused and its disposable container removed when the 32 GB
filesystem exhausted free space. Its logs, database/object-store volumes,
configuration and export ledger are retained; removing that owned stateless
container recovered about 1.2 GB. Web, PostgreSQL, Redis, ClickHouse and S3 remain
running, and the web health check passes. Restarting the full six-container stack
before capacity is increased would exhaust disk again. The native dataset is
stored and remains readable while trace ingestion is paused.

The repository now includes standard-library native dataset/diagnostic publishers;
no alternate dashboard UI or replacement billing ledger was built. The component
publisher updates its owned native dataset rows by deterministic ID. Observation
publication uses the existing immutable delivery ledger, a separate contract.

### Concrete continuation requirements

The environment policy was rechecked and still has no added custom allowed
hosts. Supported configuration must allow **api.osv.dev** for advisory checks and
**chatgpt.com** for the existing Codex route. Do not bypass the proxy. Increase
workspace disk from **32 GB to at least 64 GB** before restoring the worker and
running retained experiments. These configuration changes have been requested
from the user; no approval or exception is inferred from elapsed time.

After those changes: finish security review and remediation, reconcile the
uncertain observation batch, restore ingestion, verify the real intervention
canary, and freeze a bounded task/allocation/budget protocol. Remaining proposed
components still need implementation and their own gates. The existing package's
`REQUIRED` task/budget entries are not an executable authorization record.
No configuration yet has enough live evidence for an efficacy recommendation.
