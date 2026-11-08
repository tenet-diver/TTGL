# Smallville source fidelity and first implementation

8 November2026. This is an adapted terminal-memory implementation, not a
reproduction of the Smallville world, its original models or social evaluation.
Plan: [implementation/progress](smallville-memory-implementation-plan.md).

## What is reused

Pinned author commit `fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4`, Apache-2.0.
A complete `reverie` subtree inspection replaces the initially truncated full
repository tree.20 selected source/template/license files and one additional
triple template have Git blob and SHA256 receipts in the private source review.
The original full simulation requirements are not installed or executed.

[Vendored source map](../../tools/usage-monitor/experiments/smallville_vendor/SOURCE_MAP.json)
records upstream file hashes and each reused definition's source fingerprint.
The `ConceptNode`/`AssociativeMemory` class bodies, retrieval functions and seven
reflection functions are preserved. Only simulation/provider imports are removed;
standard-library dot/norm supplies cosine math, and callbacks supply the local
embedding runtime and native model transport. The original license and attribution
are included.11 selected prompt files are copied byte-for-byte, including the
actual v2/v3 callers and alternatives.

| Behavior | Released source and implemented primary behavior |
| --- | --- |
| Memory fields | Original node/type counts, event/thought/chat type, depth, created/expiration/access time, subject/predicate/object, description, embedding key, poignancy, keywords and filling/evidence. Terminal adapter currently exposes observations and reflection thoughts; not the complete simulation planner or chat perception. |
| Persistence | Original `nodes.json`, `embeddings.json`, `kw_strength.json` exports; adapter adds completed-snapshot pointer, operation audit and state sidecar. |
| Candidate order | Events plus thoughts, excluding embedding keys containing`idle`; ascending last-access time with original stable ties. |
| Recency | `0.99**rank`, with rank starting1 in that ascending order. This can favor older records when other components tie; preserved and tested, not silently corrected. It is not paper-described elapsed-hour decay. |
| Normalization | Original min-max per component; flat ranges become0.5. |
| Score | `0.5*recency + 3*relevance + 2*importance`, default scratch multipliers1; cosine relevance. |
| Retrieval | Original top-k default30; selected records' last-access times become current time. |
| Importance prompt | Actual v3 event-poignancy template and JSON wrapper with original social examples and identity format. `generate_poig_score` uses that event template for both events and reflection thoughts; the separate thought template is retained but not substituted. |
| Trigger | Remaining importance starts150; observed events decrement it and increment the new-event count. Reflection due at remaining<=0 with nonempty event/thought memory. |
| Focal questions | Original3-question template/wrapper; observations selected by original access ordering and new-event count. |
| Insights | Actual v2 template,5insights per focal question, zero-based numbered retrieved evidence as in the source caller. |
| Derived thoughts | Original triple-generation prompt, event-poignancy rating, local embedding, evidence IDs, depth and30-day expiration field. |
| Reset | Original counter resets to150 and new-event count0 after completed reflection. |
| Restart access | Original export does not persist last_accessed; reload resets it to creation. Primary preserves this. Optional explicit sidecar restoration is separately software-tested and disabled in the initial canary. |

## Explicit adaptations and limitations

- Authenticated cloud Codex replaces obsolete GPT API models. No sampling/temperature
  equivalence is claimed. Pinned local BGE/FastEmbed replaces the original hosted
  embedding model. No paid/hosted memory or embedding service is used.
- Native importance/reflection callbacks make one attempt. Original retry loops and
  silent failure defaults are not copied: uncertain calls are not repeated, and
  malformed ratings/citations stop with preserved evidence. Citation indices are
  validated before the original fallback could create an unsupported blank thought.
- Terminal observations are supplied as explicit model-visible event descriptions
  and subject/predicate/object values, replacing simulated environmental perception.
  The native canary uses labeled synthetic input, not measured terminal experiences.
- Original print output is captured as an audit log so it cannot corrupt tool
  transport. The original loader's unclosed-file ResourceWarnings remain visible in
  software-test output. No upstream code correction is hidden.
- Source-body fingerprints establish preservation, not efficacy. Stub callback tests
  cover storage, surprising recency order, relevance weighting, access renewal,
  restart behavior, threshold/reflection/evidence depth, namespace boundaries,
  malformed importance/citations and embedding dimensions. They are not model trials.

## Native canary registered before inference

[Protocol](../../tools/usage-monitor/studies/smallville-native-mechanism-protocol-001.json):
six synthetic repair observations scored separately, original ranking, three focal
questions and five insights each, original triple/rating calls for every thought,
then one recall reader. Expected41 calls, maximum48, no process retries. A natural
150-point trigger is unlikely with six observations; if not reached, the harness
records the remaining value and forces the diagnostic trigger. This tests actual
reflection mechanics, not natural trigger frequency or task benefit.

All normal/auxiliary native response IDs must reconcile with private captures and
Langfuse. All calls are research expense. Correct recall alone does not establish
quality/cost readiness for benchmarks. Long-horizon development and held-out
comparisons remain separate phases in the plan.
