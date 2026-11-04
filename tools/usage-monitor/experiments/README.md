# Context-compression experiment prototype

This directory belongs to the existing TTGL repository. It compares unmodified
observations, Headroom compression at insertion, and older-observation masking.
It is a small synthetic mechanism pilot, not a coding benchmark or evidence of
production savings. Existing registered routing studies are not changed.

## Security gate and current status

Further Headroom execution is blocked. A package-only scan returned no known
advisories, but the broader image scan found 85 distinct advisory IDs across
38 package entries. This count includes unscored/unimportant matches and is
not a claim that every issue is exploitable. The user's policy blocks all known
findings. Docker Scout could not authenticate; the existing OSV scanner supplied
the image report instead. No scanner was installed to perform this check.

Headroom 0.42.0 declares LiteLLM as a required distribution dependency. The
initially resolved version was 1.103.10, not the versions named in the
[March](https://docs.litellm.ai/blog/security-update-march-2026) or
[October](https://docs.litellm.ai/blog/security-incident-oct-21-2026-attack-chain)
compromise reports. This is not proof of safety. LiteLLM was removed, and the
standalone compressor smoke test worked without it. Experimental startup now
checks that LiteLLM is absent before importing Headroom.

No dependency or image is installed by these scripts. `context_pilot.py run`
requires a reviewed security receipt for the exact immutable image ID. Missing,
incomplete, expired, mismatched or finding-bearing receipts are rejected before
any model or container starts. Receipts expire within at most 24 hours; a new
installation still requires fresh checks at installation time.

The tested Headroom setting is the published SDK's `agent`/lossless mode, with
ML disabled and first-insertion results memoized. It is not a test of every
Headroom profile or the stock proxy. The offline nested-JSON probe produced no
token reduction. Earlier native code-mode filtering and unavailable-tool checks
are setup failures, not treatment results. A later pilot completed only one
inventory case for baseline and Headroom before the masking mechanism gate
failed. No complete three-arm comparison or savings claim is available.

## Files

- `context_pilot.py`: fixed read-only fixture MCP tools, offline compressor,
  local forwarding adapter and bounded native Codex runs. Official Codex handles
  subscription login; the compressor receives fixture text only, never headers
  or credentials. The forwarding destination is fixed to the official endpoint.
- `publish_context_pilot.py`: publishes finalized journals to local Langfuse
  using the existing immutable-receipt exporter. Provider usage is measured;
  setup/incomplete calls remain separate from completed fixture trials.
- `test_security_gate.py`: verifies that missing reviews, known findings, stale
  receipts and different images cannot authorize execution.

The controlled exposure task explicitly requests full marked observations.
That differs from default Codex behavior, which can filter large tool results
programmatically before the model reads them. Root task time includes CLI and
tool overhead. All retrieval/model calls count; cache reads are a subset of input.
API-price scenarios are not subscription invoices or quota savings. Local compression
weights use o200k_base through the SDK’s gpt-4o tokenizer tag; the actual trial
model is gpt-6.1-sol and provider-reported counters are authoritative.

Private journals, rollouts, credentials, package wheels and image reports stay
outside the repository. Do not commit them. Incomplete model usage is unknown,
never zero. Started or uncertain assignments must not be silently repeated.

Dependency-free local checks:

```sh
python3 -m unittest discover -s tools/usage-monitor/experiments -p 'test_*.py'
```

## Codex Cloud setup

The user selected Codex Cloud. Follow the [setup guide](../../../docs/research/context-compression-cloud-setup.md)
and run `sh tools/usage-monitor/experiments/cloud_setup.sh` for inspection-only
checks. This does not install dependencies or start experiments. The older
Codespaces notes below are background, not the requested deployment target.

## Codespaces

Use **this existing TTGL repository**, not a second repository. A disposable
Codespace improves isolation from the local computer, but does not cure
vulnerable dependencies. No Codespace was created, and no active dev-container
configuration is added while the base-image security gate is blocked. GitHub's
default dev-container is not an implicitly approved substitute.

Before launch: approve and pin the full runtime/base image, exclude personal
dotfiles and broad secrets, request no access to other repositories, and keep
ports private. Do not copy local Codex authentication files or private rollout
history. New CLI installations, extensions, dev-container features and lifecycle
commands require the same pre-install checks. Do not auto-install on creation.

Langfuse on the local computer is not `localhost` inside a Codespace. Initially
keep remote journals private and publish from the trusted local environment, or
separately configure an approved private connection. Do not expose local Langfuse
publicly to make migration work.

See [GitHub's security model](https://docs.github.com/en/codespaces/reference/security-in-github-codespaces)
and the mandatory dependency rules in the repository and global `AGENTS.md`.

## 5 November Cloud continuation

Read the [continuation and ten-idea backlog](../../../docs/research/context-experiment-continuation-20261105.md). The supplied package is preserved as reference, not execution authority. Nine offline adapter checks pass after a JSON-text serialization fix; live Headroom and masking trials remain gated.


### Offline comparisons and native dataset publication

`offline_component_study.py` compares original observations, failure-row projection
with/without recovery, older-output references and reversible handles on two
synthetic formats. It uses oracle-guided source selection and serialized bytes,
not model decisions/tokens. Projection without recovery intentionally loses details.
See the continuation record for the blocked native canary and full ten-technique status.

Publish finalized component evidence with the existing local native Langfuse API:

```sh
python3 tools/usage-monitor/experiments/publish_component_results.py --report results/context-cloud-20261105/offline-components.json --credentials "$TTGL_LOCAL_LANGFUSE_CREDENTIALS_FILE" --state work/context-pilot-cloud-dataset
```

`publish_offline_diagnostics.py` can publish finalized adapter checks through the
existing immutable observation exporter. A timed-out batch is uncertain: preserve
its outbox and reconcile, never change state directories to force a retry. Current
cloud ingestion is paused for disk capacity; native dataset rows remain readable.
