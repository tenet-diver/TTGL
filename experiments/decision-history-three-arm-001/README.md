# Decision history across fresh coding sessions

This study tests whether a fresh Luna session benefits from its predecessor's
decisions when extending independently verified code. It follows the matched
SlopCodeBench pilot and the worker feedback fault observed in its follow-up.
[Prior pilot and transport evidence](../decision-history-scb-001/README.md).

## Registered comparison

Two fresh Python lineages use different dependent requirements. Seat allocation
adds an in-place rename that must preserve activation order. Layered flags adds
an ordered reset directive while preserving falsy values and deletes. Each
lineage starts with one real native predecessor session. The host checks its
final source independently and binds an agent-reported decision and applicability
condition to the recorded public verification. The private memory admits only
that lineage's predecessor. No additional inference extracts or serves records.

| Arm | Context available to the fresh Luna session |
| --- | --- |
| Code only | Common Git snapshot, current and earlier public specifications, public tests |
| Summary only | Common context plus optional MCP access to the predecessor summary and check-linked decision |
| Full history | The same search index and records plus optional conversation pages |

Seats runs code only, summary only, then full history. Flags runs the reverse
order. Each native call uses `gpt-6-luna` at low effort through the same
subscription and pinned Codex CLI 0.170.0, with a 120-second cap and zero
automatic retries. All continuations receive the same general prompt and
offline worker, including actionable feedback for out-of-range shell timeouts.
The model-free worker control rejects 10,000 seconds, then reads a public file,
edits the candidate and passes a public test using the default timeout. Four
independent reference and empty-patch pairs qualify the two checkpoints in each
lineage. The continuation references also pass every prior check.

The primary outcome is all independent target checks passing. Earlier checks
measure preservation of predecessor behavior. Report exact check counts, native
tokens, recorded elapsed time including archival, and actual retrieval. The
original registration reserves a separate seats comparison if the optional
history arms open zero conversation pages. Two fresh sessions get the same
summary and decision access, and one also receives a bounded predecessor
excerpt in its prompt. The excerpt tests direct exposure on this case.

## Admission amendment

Both predecessors pass all four independent checks. The seats predecessor
combines its final source write and the public test in one shell call. The
original standalone-command rule excluded the handoff. Continuation 002
accepts the retained call after verifying the heredoc matches the sealed
candidate byte for byte, the final command is the specified public test, and
the result records exit zero and a passing test. It reuses the original
predecessor without another call. The three seats assignments had never started.
All solver prompts, limits, tools, grades, and ordering stay matched.

## Results

All ten native invocations reached terminal receipts. Both predecessors passed
4/4 independent checks. All six main continuations passed all four target and
all four prior checks. None of the four MCP-enabled main sessions requested
history. The offline worker recorded zero invalid timeout requests. Reported
elapsed time includes local archival, and tokens are native counters.

| Handoff | Arm | Target | Earlier | Elapsed (s) | Native tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| Flags | Code only | 4/4 | 4/4 | 15.00 | 48,127 |
| Flags | Summary only | 4/4 | 4/4 | 17.96 | 48,832 |
| Flags | Full history | 4/4 | 4/4 | 17.09 | 48,744 |
| Seats | Code only | 4/4 | 4/4 | 20.13 | 48,909 |
| Seats | Summary only | 4/4 | 4/4 | 31.35 | 61,209 |
| Seats | Full history | 4/4 | 4/4 | 18.96 | 48,899 |

The zero-read rule triggered the two-seat direct-exposure diagnostic. We
verified that the intervention's actual native prompt contained the bounded
predecessor excerpt. Both sessions retained optional access to the same
records and made zero MCP calls.

| Excerpt diagnostic arm | Target | Earlier | Elapsed (s) | Native tokens |
| --- | ---: | ---: | ---: | ---: |
| Offered summary and decision | 4/4 | 4/4 | 18.77 | 38,357 |
| Offered the same records, supplied an excerpt | 4/4 | 4/4 | 17.52 | 39,536 |

The study observed no quality difference on these two development handoffs.
All code-only agents reached the ceiling. The absence of optional retrieval
leaves the effect of acting on a decision unmeasured in the main arms. The
excerpt pair measures one instance of direct exposure at the same ceiling.
Neither this pair nor timing variation across individual sessions establishes
an efficiency or quality advantage.

The native accounting totals 468,118 tokens across all ten calls. That
includes 85,505 for predecessor construction, 304,720 for the main comparison,
and 77,893 for the excerpt diagnostic. The audit verified both report hashes
against local S3 receipts, all grades by independent replay, and all terminal
token totals against native events. It also confirmed distinct threads, matched
starting snapshots, identical search corpora within each handoff, and exact
excerpt delivery. [Public metrics and audit hashes](results.json).

## Reproduction and evidence

Source code, invocation identities, public inputs, grading controls and local S3
receipts are sealed in the private study directories. The audit replays grading
from the frozen candidate bytes without model calls and reconciles each terminal
model counter, trace hash and retrieval receipt count.

```sh
PYTHONPATH=src python -m ttgl.decision_history_study audit
PYTHONPATH=src python -m ttgl.decision_history_study_continuation audit
```

The first audit reads `work/security/decision-history-three-arm-001`. The second
reads `work/security/decision-history-three-arm-continuation-002`. The earlier
SlopCodeBench pilot retains two terminal invocations, one interrupted invocation
with a gradeable snapshot, and seven unstarted assignments. Its registered pairs
remain incomplete. The later study does not fill those missing pilot cells.
