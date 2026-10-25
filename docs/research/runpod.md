# Runpod execution plan

Status: prepared; no Runpod account call, GPU allocation, training or spending has occurred. The user selected one 80 GB GPU and authorized a maximum **US$100 total** for this experiment. Secure account connection and current price/access checks remain required before provisioning. This authorization persists; do not ask for the same budget again.

## Existing software and inspected API

Use the maintained Runpod SDK/CLI for account and resource management. Source inspected on 2026-10-25: `runpod/runpod-python@397c37d3d2a04aaa2eb3c8a83cdc359e230bcb6e`. This is a source pin, not a claim that a particular PyPI release contains identical APIs.

Current source exposes synchronous `runpod.get_gpus()` and `runpod.get_gpu(gpu_id, gpu_quantity=1)` for GPU catalog/availability, `get_pods()`/`get_pod(id)` for state, `create_pod(...)` for provisioning and `terminate_pod(id)` for deletion. Discover exact GPU IDs from the returned catalog; do not invent IDs or infer availability from a model name. Read actual current pricing and all storage/network charges before selecting an instance. No current price has been verified.

Both REST `/v2/...` and GraphQL calls in this source use `https://api.runpod.io` and an `Authorization: Bearer ...` header. `RUNPOD_API_KEY` can therefore be supplied as a proxy-backed environment secret scoped to `api.runpod.io`; never put it in source, chat, command-line literals, artifacts or saved run manifests. The synchronous transport uses `requests`, which supports the inherited proxy settings.

The new `@app.task` API creates an ephemeral pod, waits for its runner, invokes it, collects the response and terminates it. Its runner address is `https://<pod_id>-8080.proxy.runpod.net`; the runner uses a generated task token, not the account API key. If choosing this route, permit `*.proxy.runpod.net` for execution and retrieval separately from the account secret destination. Serverless endpoint calls use `api.runpod.ai`; that destination is not required for ordinary standalone-pod inventory/management.

**Transport limitation:** inspected asynchronous task/control-plane code constructs `aiohttp.ClientSession()` without `trust_env=True`. It must not be assumed to honor the session's mandatory HTTP proxy. Validate transport in the intended controller environment before choosing this path. Do not silently drop the proxy or modify routing. An existing authenticated Runpod workspace or supported remote terminal is a usable alternative for the staged shell job below.

## Bounded first run

1. Read inventory, availability and current price using authenticated read-only requests. Select one A100 80 GB or H100 80 GB and record its exact ID, hourly cost, image digest, CUDA/driver details and storage terms.
2. Convert the user-approved total budget into a maximum lifetime, reserving funds for image/model downloads, startup, export, evaluation and shutdown. Set both a process timeout and a controller-side deadline. An in-pod process timeout does not terminate billing.
3. Provision only one task-specific pod. Record its ID immediately. Avoid persistent network volumes for the first experiment unless explicitly needed; they can keep billing after compute terminates.
4. Upload the source/config/train-data bundle using the provider's existing authenticated workspace/transfer mechanism. Do not embed an account token inside the bundle or forward the cloud proxy's placeholder as a raw secret to the pod.
5. Verify dependency versions, GPU availability, model revision, data hash and a training dry run. Execute a short pilot, observe actual throughput/memory, and estimate whether the planned run fits the remaining budget. Do not extrapolate CPU replay timings to GPU training.
6. Retrieve complete adapter/config/manifests and logs, verify artifact checksums, then terminate the task-specific pod through the SDK. Verify `get_pod(id)` reports absence or a terminal state. Record actual billed cost where available. Do not stop or delete unrelated user resources.

The SDK has cleanup logic and task timeouts, but cleanup failure is possible. Keep a controller-side termination path and verify removal. A stopped pod or a retained volume may still incur storage charges; distinguish stop from terminate.

## Staging without cloud access

From the TTGL repository root, once dataset preparation has completed:

```bash
mkdir -p artifacts/runpod
tar --exclude='__pycache__' -czf artifacts/runpod/ttgl-training-source.tar.gz \
  src/ttgl configs pyproject.toml scripts/runpod_job.sh \
  data/processed/train.jsonl data/raw/livecodebench/DeepSeek-V3.json
sha256sum artifacts/runpod/ttgl-training-source.tar.gz
```

Only `data/processed/train.jsonl` is supplied to the trainer as training examples. The hash-pinned raw source is required to recover titles and starter interfaces; its metadata loader retains public prompt fields and checks exact task alignment. The raw artifact also contains published evaluation outputs, so record its presence and prevent it from being used as a training-example source. Hidden benchmark tests are absent. Review source contents before transferring; these files contain public benchmark prompts and generated code, not customer code. A stricter future packaging step can export a separately hashed metadata-only subset once that change is tested.

Inside the prepared workspace, activate a Python 3.12 environment with the exact training dependencies recorded in `configs/training-sft.json`. See the training guide for installation and the tested CLI contract. Do not install an arbitrary newer CUDA/PyTorch stack over a pinned environment merely to resolve a version mismatch.

```bash
bash scripts/runpod_job.sh data/processed/train.jsonl \
  artifacts/sft-preflight configs/training-sft.json --dry-run

# Set this value from actual price and the approved budget before execution.
: "${TTGL_JOB_TIMEOUT_SECONDS:?Set from the current quote and approved budget}"
bash scripts/runpod_job.sh data/processed/train.jsonl \
  artifacts/sft-seed1729 configs/training-sft.json --run
```

The wrapper preserves the trainer's exit status, rejects existing output paths, and requires an explicit timeout for real training. It does not create/delete pods or enforce an account-level monetary cap. Use the separate controller deadline and verified termination described above.

Expected output includes selected example provenance, a frozen model revision, dependency/config/data hashes and training manifests. Only an actual completed GPU run may record `trained`; dry-run output records preparation. Training loss or internal validation loss does not establish held-out coding accuracy. Run the coding evaluation separately before any quality claim.

## Verified locally versus outstanding

- Locally checked: shell syntax, missing-argument failure, and the training data preflight on the prepared training split: 429 input tasks, 334 verified examples retained, 95 tasks without a verified solution excluded. Manifest status is `prepared_not_trained`.
- Source-verified: synchronous authentication transport, inventory/resource method names, ephemeral task lifecycle, task timeout and cleanup behavior in the pinned SDK source.
- Outstanding: live authentication, pricing/availability, instance provisioning, GPU dependencies, model download, training, artifact transfer and billing reconciliation.

## Primary sources

- [SDK README and task examples](https://github.com/runpod/runpod-python/blob/397c37d3d2a04aaa2eb3c8a83cdc359e230bcb6e/README.md).
- [Synchronous resource commands](https://github.com/runpod/runpod-python/blob/397c37d3d2a04aaa2eb3c8a83cdc359e230bcb6e/runpod/api/ctl_commands.py).
- [REST transport and Bearer authentication](https://github.com/runpod/runpod-python/blob/397c37d3d2a04aaa2eb3c8a83cdc359e230bcb6e/runpod/api/rest.py).
- [GraphQL transport](https://github.com/runpod/runpod-python/blob/397c37d3d2a04aaa2eb3c8a83cdc359e230bcb6e/runpod/api/graphql.py).
- [Ephemeral task execution, timeout and cleanup](https://github.com/runpod/runpod-python/blob/397c37d3d2a04aaa2eb3c8a83cdc359e230bcb6e/runpod/apps/tasks.py).
- [Official train/evaluate example with network volume](https://github.com/runpod/runpod-python/blob/397c37d3d2a04aaa2eb3c8a83cdc359e230bcb6e/examples/apps/train_and_eval.py).
