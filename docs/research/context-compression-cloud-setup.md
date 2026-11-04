# Codex Cloud setup for the context experiments

Use the existing `tenet-diver/TTGL` repository and select branch **`work`**.
Read the [handoff](context-compression-cloud-handoff.md), `AGENTS.md`, and the
[dependency security policy](../security/dependency-security-policy.md) first.
This guide prepares a Cloud environment; it does not authorize the blocked
Headroom image or resume any unrelated research.

## 1. Create an inspection-only environment

In current Codex Cloud, choose **Work in → Cloud → Select environment → Create
environment**, or **Settings → Codex Cloud → Environments**. Give the environment
access only to TTGL, keep it private, and choose `work` for the task checkout.
Confirm the checked-out commit contains this guide and the setup script below.
Some legacy environment-cache setup checks out the default branch before the
task branch. If the script is missing, stop and configure the setup checkout to
`work` or reset the stale environment cache; do not fall back to installing the
full default-branch project or change the repository default branch.

Supply this setup instruction before permitting repository dependency setup:

> Prepare only the context-compression experiment tools. Read AGENTS.md and
> docs/security/dependency-security-policy.md before installing anything. Do not
> automatically install TTGL's full dependency set, Headroom, LiteLLM, Codex CLI,
> Docker, scanners, extensions or dev-container features. Run only the
> inspection-only setup script below using existing managed tools. Report
> missing capabilities rather than installing them. Keep model trials stopped
> until security receipts and intervention checks pass.

Review or replace generated install/start commands; do not accept automatic
`pip install`, `npm install`, `npx --yes`, source builds or image launches. If the
interface cannot apply these restrictions before installation, stop setup and
record that limitation. No new dependencies are needed for the initial tests.

Set the install/setup command to this inspection-only command, from the repo:

```sh
sh tools/usage-monitor/experiments/cloud_setup.sh
```

The script checks existing tools, reads package-version metadata without importing
Headroom/LiteLLM, runs four security-gate tests and 21 existing Langfuse tests,
and writes `work/cloud-setup/setup-report.json`. It does not install, download,
start containers, inspect secrets or invoke models. Missing Git/Python or failed
tests stop setup. A passing setup report is **not** a runtime security approval.

Current Cloud can save an **Install script** and a **Start skill**. The start
instructions should rerun these checks and report blockers; they must not start
Headroom automatically. Review prepared files before publishing the reusable
environment. Keep these instructions for later setup changes and republishing.

If using the legacy UI, select **manual setup** rather than automatic dependency
installation and use the same command as the setup script. Do not add a
maintenance script that upgrades packages. The current and legacy products have
different setup, networking and secret behavior; do not assume settings transfer.

## 2. Networking and credentials

Start with **no optional secrets**. The initial tests require none. Restrict
outbound destinations to what is required for the current phase: official
advisory/vendor sources for inspection, approved registries for reviewed
downloads, and the actual provider only when live trials are authorized. Do not
enable unrestricted networking just to make an installer or proxy work.

Use current Cloud's environment settings/Personal vault for approved credentials,
scoped to this environment. A network secret restricts substitution to configured
HTTPS destinations; a direct environment variable is visible to its process.
Choose the supported mechanism required by the approved client. Never put values
in Git, prompts, command arguments, setup logs or reports. Do not copy Mac
`auth.json`, SSH keys, dotfiles, Langfuse configuration files or rollout history.

Legacy Cloud secrets are setup-only and removed before the agent phase; current
Cloud has different mechanisms. Do not assume a setup `export` or legacy secret
will authenticate a later task. Use the environment's documented network proxy
and CA configuration, without disabling TLS verification.

The prototype forwarding adapter was tested on the Mac and uses a fixed official
Codex HTTPS endpoint. It may require a supported networking adaptation in Cloud.
Verify the actual runtime, Docker daemon, CLI and authentication capabilities;
binary presence alone does not establish that they work. The Cloud agent's own
model access does not imply that a nested Codex CLI has authentication. If the
supported metered client is unavailable, record the blocker rather than copying
tokens or fabricating usage.

## 3. Review a runtime before installing or executing it

Use existing approved scanners where available. Resolve the full graph from
metadata or download-only operations with scripts/builds disabled. Check current
package and base-OS advisories, publisher incidents, hashes/provenance and
automatic-execution hooks. Save raw evidence and a dated receipt under ignored
`work/security/`. Do not install a scanner to bootstrap this process without
reviewing that scanner first.

The old experimental image remains blocked: removing LiteLLM did not remove its
85 OS/image advisory IDs. No clean replacement is provided by this guide. Do not
write a passing receipt until all required evidence actually supports it.

The launcher requires these receipt fields:

- `decision`: `pass` only after review, otherwise `blocked`.
- `image_id`: the exact immutable `sha256:...` local image ID.
- `checked_at` and `valid_until`: timezone-aware timestamps, maximum 24-hour
  validity. New installations still require checks at installation time.
- `full_graph_reviewed`, `os_image_scan_complete`,
  `malicious_release_review_complete`, `artifact_integrity_verified`,
  `scripts_reviewed`: all true only when evidenced.
- `known_findings`: an empty list only after a complete clean check. Unknown
  findings or unavailable scanners are not a clean result.

The receipt is an agent-reviewed record, not a cryptographic attestation or an
OS-wide installer block. Cloud isolation does not override the security policy.

## 4. Validate, then register fresh trials

First test fixture exposure, Headroom invocation and older-result replacement
without scored inference. Account for native tool-host filtering and context
references/deltas. A non-applied intervention is a failed mechanism check, not
zero savings. Preserve native reasoning and call IDs.

After the runtime and method pass, register a fresh bounded protocol and run ID.
Keep model, effort, tasks and quality checks matched, and include cache misses,
retrievals, failed calls, compression overhead and task time. Do not silently
retry or resume uncertain Mac assignments. The existing launcher is a prototype;
its masking gate failed previously, so an approved image alone is insufficient.

For a reviewed, already available image, the launcher shape is:

```sh
python3 tools/usage-monitor/experiments/context_pilot.py run \
  --root work/context-pilot-cloud-001 \
  --image "$TTGL_APPROVED_IMAGE_ID" \
  --security-receipt work/security/approved-runtime.json
```

Do not run this with the old image, missing evidence or a fabricated receipt.
The launcher refuses missing/stale/mismatched/finding-bearing receipts and never
pulls an image automatically. Its current actual model is `gpt-6.1-sol`, low
effort; an unavailable model requires a disclosed protocol change, not silent
substitution. CLI authentication uses its supported flow, never copied Mac files.

## 5. Save results and publish safely

Keep private journals and receipts in the ignored `work/` locations. Retain the
protocol, source/image/dependency hashes, provider request counters, per-stage
answers/checks, retrieval counts, failures and unknown usage. Summarize completed
trials separately from setup/incomplete calls in JSON/CSV. Do not commit raw
journals or private usage tables to public TTGL.

Langfuse at the Mac's `localhost:3000` is not reachable as Cloud localhost.
Use a separately approved private connection, or export the private result bundle
for publication from the trusted Mac. Do not expose Langfuse publicly or copy its
keys into the repository. The existing publisher accepts a local credentials
file and finalized journals; preserve its delivery ledger to avoid duplicates:

```sh
python3 tools/usage-monitor/experiments/publish_context_pilot.py \
  --root work/context-pilot-cloud-001 \
  --credentials "$TTGL_LOCAL_LANGFUSE_CREDENTIALS_FILE"
```

That publication command runs where the approved local Langfuse connection and
private credential file exist, not automatically in Cloud. Without such access,
leave JSON/CSV in private Cloud outputs and report that publication is pending.
Do not build another UI or restart the paused historical research heartbeat.

Official references, checked 5 November 2026:

- [Current Cloud environments and setup](https://learn.chatgpt.com/docs/environments/cloud-environments)
- [Legacy setup, caching and secret behavior](https://learn.chatgpt.com/docs/environments/cloud-environment)
- [Security guidance and environment distinctions](https://learn.chatgpt.com/docs/enterprise/security-cookbook)
