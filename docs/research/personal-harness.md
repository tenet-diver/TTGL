# Codex conversational-agent experiment harness

`ttgl.personal` adds a bounded experimental controller around the existing Codex CLI for **We have to combine — A conversation is all you need**. The testable hypothesis is lower total cost with minimal task-performance loss, not a claim that conversation is already sufficient. Codex still performs repository inspection, editing, shell execution and test execution. The module supplies condition assignment, a continuing small/large-agent conversation, persistence and measurement; it does not implement another coding-agent loop or claim that this orchestration is a novel algorithm. Personal memory is optional and defaults to an empty list.

Four conditions are implemented:

| Condition | Behavior |
| --- | --- |
| `small` | One Luna agent solves the task with tools. |
| `large` | One Sol agent solves it with the same tools and initial memory. |
| `precall_router` | Luna selects small or large from task text and memory before any solving attempt; the selected agent then solves alone. Router usage is included. |
| `personal` | Luna acts in the workspace, optionally converses with Sol, resumes its own Codex thread, and verifies/integrates useful proposals. Sol can ask for context or challenge Luna; both sides retain their conversational threads. |

The pre-call condition is a simple LLM routing baseline. It is **not an implementation or reproduction of RouteLLM, Router-R1 or a calibrated success predictor**. Astra can replace Sol through `--large-model gpt-6-astra`; every such change defines a separate condition. Requested model identifiers do not establish provider availability or immutable weight revisions. Log the service version when the provider supplies it.

## Execution

Use a working Codex installation and its existing supported authentication. Run the experiment in independently reset repositories with benchmark graders and reference patches outside the agent environment. Do not place credentials in task metadata or prompts. The current managed environment has `codex-cli 0.163.0`, but its nested `codex exec` probe failed during app-server initialization because a required filesystem location is read-only. No model call through this adapter has been validated here. The current in-product Codex collaboration tools are a separate execution interface; a manually orchestrated pilot through them must record that distinction.

Create a task JSON file such as:

```json
{
  "task_id": "example-repair-001",
  "prompt": "Fix the reported conversion bug and execute the available regression tests.",
  "workspace": "/absolute/path/to/reset-task-repository",
  "allowed_paths": ["src", "tests"],
  "memory": [
    {"id": "compatibility", "text": "Preserve public API names and existing serialized formats."}
  ]
}
```

Run one condition in a new output directory outside that repository:

```bash
python -m ttgl.personal \
  --task /absolute/path/to/task.json \
  --condition personal \
  --output-dir /absolute/path/to/results/repair-001-personal \
  --small-model gpt-6-luna \
  --large-model gpt-6.1-sol \
  --reasoning-effort medium \
  --max-expert-calls 2 \
  --max-turns 6 \
  --timeout-seconds 900
```

The same initial task memory, prompt, allowed paths, effort setting and wall-time budget belong in every matched condition. Each condition needs a fresh workspace reset; this module deliberately does not reset or delete repositories. The expert receives only the question/context that the small agent chooses to send throughout their conversation. Both agents keep their own Codex thread, so the second expert request resumes the first expert conversation rather than starting a stateless call. An oversized question/context fails explicitly instead of silently losing information. The default combined limit is 24,000 characters per message, an application transport bound rather than a tokenizer-based limit on the accumulated conversation.

The expert's structured response has `action` equal to `answer`, `request_context` or `challenge`, plus a natural-language `message`. The small agent can inspect code and execute checks before replying, answer a clarifying question, disagree with the expert, supply a counterexample or request a revised proposal. It returns `ask_expert` with its latest message in `question` and relevant evidence in `context`; that message continues the same expert thread. For example: small agent proposes a change → expert asks about caller semantics → small agent inspects callers and supplies evidence → expert revises its proposal → small agent tests and integrates it. This five-turn path uses two expert consultations and fits the default bounds. An expert challenge does not force acceptance or automatically terminate the task.

The current implementation has one eligible expert model per run. Its identity is fixed in the configuration; a changed model requires a new condition/run and never silently reuses another model's thread. Multi-expert selection is an optional extension, not an implemented experiment. Even if an expert asks for more context on the last permitted consultation, the hard cap remains: the small agent must continue without further expert calls or finish with a recorded resource-limit failure. No claim of learning, personalization or many-to-many coordination is required to use this conversational condition.

`max_turns` counts Codex CLI invocations. One invocation may contain multiple internal model requests and tool calls. This is **not** a raw model-call or dollar-cost ceiling. The harness enforces the overall wall deadline and at most two expert consultations. A timeout terminates only its subprocess group, including child commands; ending the CLI cannot reverse an already billed provider request. `approval_policy="never"`, disabled web search and `workspace-write`/`read-only` sandboxes are passed to Codex. No sandbox bypass is used. Provider spending still needs an appropriately authorized account and limits outside this harness.

## Persistence and privacy boundaries

Each run writes:

- `task.json` and `memory.json`: the initial task and editable-memory snapshot;
- `events.jsonl`: an append-only request/response journal;
- `state.json`: an atomically replaced checkpoint, including the next phase and exact controller thread ID;
- `manifest.json`: final disposition, version/configuration hashes, observed usage and grading status.

Research artifacts contain the supplied task, memory and selected collaboration messages. Store these private artifacts accordingly; the harness does not infer that user memory may be published. Tool command/output bodies are not copied into the journal: hashes, execution statuses and exit codes are retained. Reasoning items are excluded. Temporary raw Codex output is discarded. No credential values or process environment dumps are written by the recorder.

Memory remains ordinary editable application state, separate from model weights. Editing a fact should update a subsequent task's memory, not trigger retraining. A changed task, initial memory, configuration or orchestrator source hash cannot resume an existing experimental run; use a new run and record the intervention. The present implementation does not learn a delegation policy, automatically rewrite durable memory, or train an adapter. Those require separately registered development data and an evaluation protocol.

Codex CLI sessions must persist in the installation's normal session storage for `exec resume` to work; therefore this adapter does not set `--ephemeral`. The module does not relocate or modify `HOME` or `CODEX_HOME`, extract authentication, or bypass the configured proxy. Do not assume these sessions or live processes survive an environment snapshot.

The task workspace and `allowed_paths` are validated against path traversal. **Allowed-path editing, context-only expert reading and benchmark-file exclusion are also instructions, not a complete filesystem security boundary.** A read-only sandbox prohibits writes but may still permit reading files outside the current directory. Expert/router turns run in an empty context directory and are told not to use tools. Observed command, file-change, MCP or web-search events from those turns invalidate the condition; that does not prove the absence of every possible tool call or external context. For confirmatory or sensitive runs, place each role in a properly isolated container/environment with only its intended inputs. Audit attempted tool use and access separately. The module must not be described as preventing cross-task leakage in this shared environment.

## Resume and failure handling

`--resume` returns an already finalized manifest without repeating calls. Between completed turns, it resumes the stored phase, subject to the original wall deadline. If a process died while a turn was in flight, the journal cannot prove whether that invocation changed files, incurred cost or completed remotely. The harness refuses automatic replay and requires manual reconciliation of the Codex session, workspace and provider record. It does not offer a force-retry flag that could silently duplicate work. Create a separately labelled attempt if recovery cannot establish the prior state.

Malformed structured responses, missing controller/expert thread IDs, unexpected expert-thread changes, forbidden expert requests by a solo condition and transport failures receive explicit terminal dispositions. Failing shell commands remain recorded diagnostics: an expected failing regression test does not by itself invalidate an otherwise successful agent attempt. `completed_ungraded` means only that the model completed its protocol. It is not an accepted patch, a benchmark pass or verified constraint satisfaction.

## Measurement and source contract

The adapter reads the documented Codex JSONL events: `thread.started.thread_id`, final `item.completed` items of type `agent_message`, and `turn.completed.usage`. Missing counters remain `null`; a missing counter in any turn makes its complete-run total unknown, while observed partial totals remain available. Input, cached input, cache-write input, output and reasoning-output tokens are separate reported categories. Do not blindly add overlapping categories or derive billing without the provider's accounting rules. Task cost is `null` because this module has neither invoices nor a verified billing model. Model-call counts, latency, token usage and dollars must not be interchanged.

The interface was checked against the installed CLI help and the following official source snapshot, retrieved on 26 October 2026 (Europe/Amsterdam):

| Source at `openai/codex@970111f6cb62cc02fe36a82ea7d71b37a2889c97` | SHA-256 |
| --- | --- |
| [events.ts](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/sdk/typescript/src/events.ts) | `dca9d5a0c216eff99f242067814be1985c027e64bf38ab4a6b6fe5c2571a4403` |
| [items.ts](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/sdk/typescript/src/items.ts) | `baee8195a8b1820301973ead2bc33678ac50886823b5ab65360f7e5d6d35ffea` |
| [exec.ts](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/sdk/typescript/src/exec.ts) | `0df2fe1ccd90e05b2f2fb0cb3e1bd3293e23f36e3bbb369258edc6a63ae8655c` |
| [cli.rs](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/codex-rs/exec/src/cli.rs) | `66643e8b3d5964b70cb8f231fb309312376272fb3ea87bcb6849f44cf112f8f6` |

The installed CLI version and adapter source hash are recorded in each new run. The source snapshot establishes the event contract, not equivalence between every future Codex release and the installed binary.

Run the meaningful offline checks with `python -m pytest -q tests/test_personal.py`. They exercise one- and two-round conversations, expert clarification/challenge followed by a small-agent reply, preservation of both threads, verification/integration prompts, matched initial memory, pre-call selection, unknown usage, failed attempts, idempotence, interrupted-call refusal, resource bounds, invalid responses, path checks, JSONL parsing and real subprocess timeout cleanup. Scripted backend responses and fake subprocesses are software tests, not model-performance results. A production readiness claim additionally requires a real authenticated end-to-end Codex invocation, the intended sandbox and an independent benchmark grader.
