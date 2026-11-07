# Cache-aware reuse: registered controlled comparison

Status: registered reuse001 running; no reconciled score yet. The completed
24-case validation and neutral judgments remain frozen. The protocol and source
manifest were committed and pushed before the first model invocation.
It addresses a limitation of the completed one-query-per-history Mem0 block:
extraction is paid once, but subsequent queries may also make the full-history
control cheaper through cached prefixes.

Use three freshly generated corpora with independently checkable facts and four
new questions each. Compare the same underlying information through continued
native full-context conversations, fresh full-history sessions with stable versus
changing prefix layouts, ordinary file search, exact FTS excerpts and the already
reviewed adapted Mem0 dense runtime. Keep raw files available equally, preserve
contradictions/dates, and hold model/effort and common instructions fixed. These
are mechanism diagnostics, not coding benchmarks or official memory scores.
Actual long-horizon code-edit transfer remains separately required.

Run actual queries and extraction, rather than extrapolating an amortization
curve. Count extraction once per real corpus, every answering/recovery/integration
call, local embedding/indexing runtime and all failed calls. Report cold-start,
per-question and cumulative complete-system model-rate cost; monetary local
compute remains unknown. Continued native full-context control is essential:
compare with its observed cache reuse rather than assuming every large prompt
is charged as fresh input. Schedule/order and any case-family separation must
be frozen; no stopping at an advantageous reuse count.

The current native CLI's continued-thread accounting was actually checked in
[native-resume-metering-001](../../tools/usage-monitor/studies/native-resume-metering-results-001.json).
Two model calls share one exact thread and two unique native responses. CLI
snapshots are cumulative: input24,411 then48,852, while the second turn itself
uses24,441 input. The complete study total is48,866 native tokens, not the sum
of both displayed snapshots. Both positive counters reconcile with native
per-turn records. Both calls (0.38498 published-rate scenario credits) are
research expense, not savings. Future reuse trials must price deduplicated
native responses or validated deltas. Actual cash/quota effects stay unknown.

For model-facing tool-output interventions, the existing HTTP/SSE adapter and
raw-source CLI have a clean actual gate in archive-native-canary005. Whole-history
age masking still needs its own application check. The maintained native
[PostToolUse hook interface](https://learn.chatgpt.com/docs/hooks) is another
integration candidate: documented feedback replacement could avoid relying on
HTTP-visible schemas. Its requested-output-update field is unsupported, so it
cannot be treated as a working replacement API. No hook has been installed or
executed for this study; native trust, result shape, raw recovery and full token/
cache cost would need separate checks before scored inference.
