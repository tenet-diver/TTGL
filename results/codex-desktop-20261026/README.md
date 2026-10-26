# Desktop host validation, 26 October 2026

The existing six-condition runner was initialized on branch `work` and its
two-call live preflight passed using the ordinary ChatGPT-authenticated desktop
Codex installation (`0.163.0-alpha.10.2`). This supersedes the prior host's
read-only startup blocker for this host only. Frozen historical results are
unchanged.

| Requested model | Input tokens | Cached input | Output tokens |
|---|---:|---:|---:|
| gpt-6-luna | 17,423 | 0 | 26 |
| gpt-6.1-sol | 18,933 | 0 | 26 |

Both returned the schema-valid preflight completion, with no tool events or
usage-accounting issues. Read `study/preflight.json`, each preflight manifest,
and its event journal for direct evidence. These calls are setup overhead,
not scored benchmark attempts or evidence of quality/cost savings. Dollar
costs remain unknown. The subscription collector queried both finalized,
independent threads; the backend returned no credit estimates, so both values
remain null in `subscription-usage.json`. Python 3.12.14 and NumPy 2.3.5 came from the desktop
bundled runtime; this is not the pinned research-analysis environment.

No scored assignment was launched. The host filesystem had approximately
12 GiB available, below the handover's 120 GB evaluation prerequisite. Docker
20.10.23 was reachable, reporting x86-64 and approximately 8 GB memory. Worker
dependency provisioning, independent read isolation, and official base/gold
controls remain prerequisites. No existing Docker resources were deleted.

The study freezes all 12 tasks and six conditions. Its `ready` preflight flag
establishes model access and token counters only; it does not establish that
the host is ready for scored execution. The worker path is recorded in the
design. Preserve these preflight records, and use a new study if source,
model configuration, or environment design changes.
