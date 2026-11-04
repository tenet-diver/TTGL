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
