# Experimental Luna / Sol adapter for SWE-bench Pro V2

Status: the adapter and observable tool recorder are implemented. Transport and
actual Harbor API callbacks pass six mechanism checks, using scripted model and
environment fixtures. **No Pro model trials or Pro environment controls have
run yet.** The first reserved development task is prepared for independent
controls. These checks establish wiring, not software-task accuracy.

The current proprietary held-out study must finish before another grader starts.
Do not overlap benchmark workers or image cleanup across studies. The reserved
Pro design uses 12 development tasks, then 24 disjoint validation tasks; it does
not schedule the full 642-task population.

## Maintained components and missing integration

Harbor 0.25.0 owns environments, lifecycle and the official task verifier. The
unchanged pinned Pro `PatchReplayAgent` supplies authoritative fresh-container
grading. `ttgl.harbor_agent:ConversationalCodex` adds only our existing controller
and its transport. Codex runs on the host using ordinary subscription login;
authentication files are not installed in the worker. The acting controller's
only repository tool forwards to its assigned Harbor `environment.exec`. Expert
roles receive no worker tool. Host shell, apps and browser tools remain disabled.

The host bridge uses an authenticated loopback endpoint and the official MCP
SDK. Its trace records bounded visible tool requests and observations with the
model request identity. It never records private model reasoning or grader
feedback. Authoritative prompts, tokens, manifests and traces go to an explicit
host records directory outside Harbor's potentially mounted agent logs. The
submitted patch remains a normal Harbor `agent/model.patch` artifact.

Before model trials, prove the actual container boundary, offline agent phase,
exact source/image provenance, empty/reference controls, patch capture/replay,
host-record invisibility, and positive native usage on the real runtime.
Synthetic fixtures do not substitute for those checks. Freeze all source,
prompt, tool, runtime and configuration hashes before scored inference.

## Reproduce mechanism checks

Use a separate Python 3.12 environment. The Intel macOS runtime is frozen in
`requirements-harbor-macos-intel.lock`; its cryptography pin is the compatible
prebuilt universal wheel, rather than relying on the host's old Rust compiler.
This environment does not replace the primary research environment or install
GPU/training packages.

```bash
python3.12 -m venv .venv-harbor
.venv-harbor/bin/python -m pip install -r requirements-harbor-macos-intel.lock
npm ci --prefix tools/worker-mcp
PYTHONPATH=src .venv-harbor/bin/python -m pytest -q \
  tests/test_harbor_agent_optional.py tests/test_harbor_bridge.py
PYTHONPATH=src .venv-harbor/bin/harbor agent schema \
  ttgl.harbor_agent:ConversationalCodex
```

The six checks cover authentication and request limits, official MCP transport,
context-only tool exclusion, and real Harbor callbacks for all three conditions.
The conversational fixture includes an expert call and verifies that expert and
integration tokens enter both total and per-model accounting. No model endpoint
is called. `results/swe-pro-prompt-001/adapter-validation-002` records the proof
scope, source hashes, runtime freeze, schema and first-task preparation receipt.

## Prepare and validate one task first

`scripts/prepare_pro_harbor_task.py` downloads an explicitly reserved task and the
official replay adapter, verifies every file against its pinned upstream Git
blob, and preserves executable modes. Its output must be outside the research
repository and all acting workspaces. Reference solutions and verifier files
remain in this private evaluator location. Only instructions reach the model.

Run Harbor's `nop` and `oracle` agents in separate fresh environments on this
single-task directory before any model trial. Use one concurrent task, one
attempt, zero retries, unique job names and retained receipts. Both command
success and native per-task reward must be inspected: empty must fail and
reference must pass. Stop on ambiguous/infrastructure outcomes; do not silently
repeat paid inference or replace tasks based on model outcomes.

After boundary and control validation, a model trial uses the custom agent with
`--ak condition=small`, `large` or `personal`, and `--ak policy=adaptive` or
`fallback`. `--ak private_records_root=/ABSOLUTE/UNMOUNTED/RECORDS` is required.
The native task budget is 3000 seconds, with at most 2940 seconds for our
controller to reserve patch-capture time; six outer turns, two expert calls,
24000 selected context characters and medium reasoning effort are fixed.
Different budgets from the earlier Verified pilot are disclosed, not pooled.

Capture and independently regrade every model patch on a pristine image using
the official pinned replay agent. Report initial and fresh grades separately,
using fresh grades for accuracy. First execute one full development block and
measure actual model tokens, scenario cost, runtime and disk needs before
expanding. All controller/expert/integration calls count. Missing usage or bills
remain unknown; Harbor `cost_usd` is not filled with a token-rate scenario.
