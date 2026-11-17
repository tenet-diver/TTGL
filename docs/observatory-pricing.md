# API-equivalent estimates and retained outcomes

The 16 November repair reconnects the already archived `task_process_results`
records to their existing analyses and subtasks. It runs no new model calls.
Reasons, confidence and source event IDs come from those original interpretations.
Citations must belong to the corresponding group. Process-v1 did not record a
separate lifecycle: `done`, `failed` and `dead_end` map to completed work,
`in_progress` maps to working, and unknown remains unknown. A completed lifecycle
does not establish a successful outcome or user acceptance. The original records
remain in S3, archived PostgreSQL rows and the untouched SQLite source.

`apps/web/scripts/repair-legacy-process.ts` previews the repair by default;
`--apply` commits it with before-images and source references in the audit log.
Repetition changes no already repaired interpretation. New imports run the same
adapter after event delivery. Modern process-v2 results and user acceptance fields
are not overwritten. The current source contains 1,245 task process results and
1,896 subtask process results. Of the subtasks, 1,603 are done, 11 failed, 20 in
progress and 262 explicitly unknown. Another 34 pre-protocol subtasks have no
retained process label. Missing/uncertain evidence is not filled with success.

The dated, editable scenario is
`apps/web/config/api-pricing-20261116.json`. The [official model pages](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
and [Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna) were
checked on 16 November. Standard USD rates per million tokens are:

| Model | Ordinary input | Cached input | Output |
| --- | ---: | ---: | ---: |
| GPT-6.1 Sol | 2.00 | 0.10 | 10.00 |
| GPT-6 Luna | 0.10 | 0.01 | 0.50 |

For Sol requests above 272,000 input tokens, the whole request uses 4.00 input,
0.20 cached input and 15.00 output rates. The threshold applies to total request
input including cache reads, not just its new tokens. This follows the model's
[published long-context rule](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

With no separately recorded cache writes, the base estimate is
`((input - cached) * input_rate + cached * cached_rate + output * output_rate) / 1e6`.
Cache hit rate is measured cached input divided by measured input. Cache reads
are already part of input and are not added again. Explicit writes, when recorded,
are removed from ordinary input and priced separately. The configured flat write
scenario selects the [published 30-minute write rate](https://developers.openai.com/api/docs/pricing).
Unreported writes stay unclassified input at the ordinary input rate; their
separate surcharges are unmeasured and excluded. The native missing write counter
remains null. The token chart places that unclassified input in Other input so
input/output totals still reconcile without inventing a cache-write count.

These are current-rate scenarios for historical usage, not historical invoices,
subscription cash, quota savings or predictions of a particular service tier.
No Fast/Ultrafast, Batch/Flex or regional setting is inferred. All 7,575 recorded
generation events have the counters needed for the configured base scenario.
Turns without retained model tokens remain Unmetered; unsupported model/rate or
counter combinations remain Unpriced. A tool-only group is not assigned an
invented share of its surrounding model's cost.

Fresh migrations/imports seed only the pristine empty pricing setting. User rates
are preserved. Editing rates also retains the date, sources, assumptions and
long-context rules. Native counters and frozen study pricing scenarios are unchanged.
