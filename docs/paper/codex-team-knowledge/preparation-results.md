# Preparation evidence — 11 November 2026

These are observed development controls and mechanism checks. **The coding-team
comparison has not produced results yet.** Preparation runs are not substitutions
for verified coding assignments, and their different workloads cannot estimate
team speedup.

| Check | Observed outcome | Interpretation |
| --- | --- | --- |
| SimPy base/reference, reviewed Python 3.11 runtime | Base: 57 failures, 83 passes. Reference: 140 passes; 10 benchmark tests deselected by repository configuration | Usable development task control; runtime differs from dataset Python 3.10 |
| TinyDB base/reference, same runtime | Base fails importing a stub. Reference: 200 pass, 1 prescribed skip | Usable development task control |
| Native Codex parent plus one child | Shared-file task and read boundary pass; all owned thread counters reconcile | Delegation and recording work; 78,074 native tokens |
| Native parent plus three children, official MCP memory | Every child reads the parent observation and writes its own record; all four exact observations retained; counters reconcile | All-member shared knowledge is observable; 293,084 native tokens |
| Official MCP memory, eight independent processes | Concurrent writes, peer reads, revision visibility, isolation and persistence pass | Storage concurrency works without auxiliary model inference |
| Local embeddings, actual Graphiti OpenAI embedder | Three finite 384-dimensional vectors; related/unrelated cosine similarities 0.963/0.409 | Local API compatibility for this synthetic example |
| Actual Graphiti OpenAI reranker, local Qwen | Relevant procedure ranks above unrelated passage, 10.39 s for two requests | Plain-text/log-probability transport works for this example |
| Local Graphiti structured extraction, three synthetic cases | 3/3 schema-valid, 3/3 correct command/verification fields; **1/3 registered exact matches** | Two project names changed capitalization; strict gate fails |
| First actual Graphiti ingestion | Stops after one successful model response when a later call requests 16,384 tokens above the provider limit | Deployment compatibility failure; ingestion/retrieval not established |

The two native delegation diagnostics took 25.214 s and 48.407 s for their
recorded parent turns. They have different instructions, worker counts and
tools, so **these times are not a scaling comparison**. Their combined 371,158
native tokens are research overhead, separate from any coding trial. Cached
input is already included in input; reasoning is already included in output.
Subscription cash expense is unknown.

Auxiliary inference uses local Qwen weights and local BGE embeddings. Codex is
still the remotely hosted coding solver. The provider uses pinned Transformers,
Torch and LM Format Enforcer, with a disclosed upstream compatibility patch and
a small HTTP adapter for missing schema/log-probability transport. This is an
adapted provider, not an unmodified Transformers serving deployment. The
reranker's numeric logit-bias IDs refer to the served Qwen tokenizer; they are
not translated from a GPT tokenizer.

The 1.7B local candidate completed one correct 551-second response; two further
requests have unknown completion usage after timeout and termination. Those
unknown costs remain unknown. Smaller-model checks are separate candidates,
not matched throughput comparisons. The stock server did not enforce the
requested schema and schema-echo responses failed validation. The constrained
provider subsequently improved format compliance without resolving exact
identifier fidelity. No candidate outcome has been silently replaced.

The reviewed llama.cpp binary remains unexecuted because confirmed applicable
findings were identified. Neo4j Community 2026.10.2 runs in a disclosed
server-only profile: the optional Parquet bundle containing affected shaded
Jackson copies is physically excluded. Actual Cypher create/read/delete passes;
fleet management and discovery are confirmed disabled. This is not a claim of
complete security clearance or vendor certification. Dated scans, hashes,
source manifests and failed preparations are retained privately.

A separate **single-agent TinyDB feasibility unit** completed with a 30-minute
deadline, 80 shared terminal calls and a two-million-observed-token stop
threshold. In-flight inference can exceed the threshold and remains counted.
It finished in **244.42 seconds**, using 18 terminal calls and **726,995 native
tokens** (718,708 input, including 646,528 cached; 8,287 output, including 522
reasoning). All 21 unique response records reconcile against unchanged transport
captures and RPC counters. Independent source-only replay passes **200 tests,
with 1 prescribed skip**. No tests or other prohibited artifacts changed. This
is development evidence, not a cell of a completed factorial study. Native
Codex supplies orchestration; a common fixed-container terminal supplies
repository execution. This constrained tool profile differs from full product
defaults. The public tests guide the solver; independent replay restores the
sealed tests and submits only implementation files.

The initial four-arm matrix remains prospective. Graphiti and Cognee need
end-to-end readiness checks before admission. Official MCP memory is a possible
additional existing-software control; adding it requires a recorded design
amendment before scored assignments. Development findings will not tune the
twelve reserved evaluation libraries. Task repetitions, final arm availability,
budgets and execution order must be frozen before that comparison starts.

The [24-assignment scaling pilot](../../../experiments/codex-team-knowledge-001/scaling-pilot-protocol-002.json)
is now frozen and running: two development libraries × native/notebook/official
MCP memory × capacities 1/2/4/8, one attempt per cell, randomized order. Each
team gets 30 minutes, 80 terminal calls, and a four-million-observed-token stop
threshold (in-flight and compaction usage can exceed it). The earlier standalone
feasibility run is excluded. Native messages and self-created Markdown notes
remain available in every arm. This compares added knowledge interfaces and
guidance, not communication against no communication. Actual worker counts
must accompany allowed capacity. The twelve evaluation libraries remain unused.

After the first two comparative completions, seven interrupted streams in the
four-agent run had no final usage. The original accounting gate stopped the
queue. Official per-thread estimates returned `null` for all four threads;
authenticated read-only retrieval returned 404, with a successful model-catalog
positive control. [Amendment 003](../../../experiments/codex-team-knowledge-001/scaling-pilot-protocol-003.json)
continues only the unstarted 22 cells, with generation, prompts, order and
evaluation unchanged. Both earlier outcomes, the stop and the original audit
remain preserved. Unknown-cost streams are retained and totals stay null; known
completed-response usage is a lower bound. Quality/time can be compared, but
incomplete cells do not support total-cost rankings. The cause of every client
cancellation is not independently established.

An amended local Graphiti ingestion check accepted the stock 16,384-token
requests but failed after **533.34 seconds and five metered responses**, with
9,682 local tokens. Edge extraction repeatedly returned truncated invalid JSON;
Graphiti's own four-attempt retry wrapper ran and is included. Provider/SDK
retries were zero. This distinguishes assignment retries from a memory system's
internal recovery behavior. No graph coding-success score is inferred.

Cognee's pinned official MCP lock contains advisory-matched dependency versions,
including both locked `unstructured` alternatives. A new **284-package**
resolution updates that package and selects current CPU Torch, but still
requires `transformers==4.57.6`, which has confirmed advisory matches. The
patched Transformers major version conflicts with Cognee's `huggingface-hub<1`
constraint. Neither affected graph was installed. This is a deployment gate,
not evidence that Cognee hurts coding quality. Local auxiliary services were
stopped before the comparative coding run to avoid CPU inference contention.

The twelve reserved libraries' base/reference archives have now been downloaded
as data for future environment checks. No held-out model assignment or prompt
tuning has occurred. Initial advisory matches in PyJWT and Marshmallow require
source applicability review and exclusion if confirmed; other dependency and
reference gates remain pending. Asset preparation is not validation evidence.

Raw receipts reside in the ignored local directory
`work/security/codex-team-knowledge-20261110/`. They include prompts, original RPC,
owned rollouts, provider requests/responses, immutable attempt records and sealed
control logs. This public summary deliberately contains no credentials or raw
private source history.


FP32 diagnostic 006, 11 November: the exact second ingestion 002 request now
completes in 76.5675 seconds, using 2,109 input and 123 output tokens (2,232 total), retaining the exact command.
The same model/BF16 profile had truncated after two tokens under 90 seconds. This supports
a runtime bottleneck explanation for that request, not full Graphiti readiness.
A new ingestion 003 fails before provider delivery: the provider exits with status 143 after
its completed diagnostic, cause unknown; no OOM kill is recorded. The request
never reaches generation, so its zero local inference is specifically verified,
not inferred from missing logs. All earlier failures remain preserved.


Reserved MiniTorch readiness 001 (zero model calls): a declared newer
Python 3.14.7 / Numba 0.68.1 / NumPy 2.5.4 environment executes the untouched tests.
Base fails collection as expected. Reference yields 15 passed, 211 failed and 4 xfailed;
all 211 failures are explicit NotImplementedError in the pinned educational
reference. This is not evidence that the newer runtime caused those failures.
The task is not admitted; tests are not weakened and no solver failure is
recorded. Its source archive lacks a root license, so none is redistributed.


Local provider phase 009 / Graphiti ingestion 005, 11 November: lossless FP32
checkpoint sharding and installed PyTorch dynamic INT8 Linear conversion make
the CPU provider ready. This is an adapted provider using a deprecated PyTorch
API, not a stock serving system or a new memory algorithm. Conversion verifies
every tensor round-trips exactly to the original pinned BF16 weights. A saved
request completes but omits the command. The real Graphiti ingestion-and-search
cycle completes in 88.2908 seconds with two LLM requests, using 3,312 input and 212 output tokens (3,524 total),
but fails the registered fidelity rule: it returns `Alice FEELS HAPY ABOUT Bob's
Promotion`, absent from the episode, rather than the verified command/project.
This candidate is not admitted to coding trials. No provider call is silently
repeated, and earlier successful extraction and failed preparations remain.
Auxiliary services are stopped after the diagnostic. It does not establish
that Graphiti with a stronger local model would fail.

A deeper native-component check places the lxml 6.1.3 runtime on hold despite its
clean Python-package scan: bundled libxml2/libxslt upstream tags have OSV matches.
Some libxslt vendor fixes are documented, but not all matches are verified as
patched. Previous independent readiness controls remain; no scored solver used
that runtime. The new Alpine compatibility profile excludes lxml and Setuptools
entirely; XML-dependent Parsel is not admitted while this is unresolved.
