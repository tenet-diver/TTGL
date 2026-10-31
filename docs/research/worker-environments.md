# Worker dependencies for the Luna/Sol development experiment

The original bridge created a clean source checkout, but a checkout alone does
not contain the historical Python dependencies required by SWE-bench. The
official evaluator image solves the evaluator's dependencies, not the host
Codex process's dependencies. Running modern host Python against old source can
produce environmental errors that look like model failures.

`ttgl.worker` reuses the **official SWE-bench task image** as a separate tool
container for each assignment. It does not install or authenticate another
agent, build a coding loop, or implement benchmark tests. Codex remains the
existing agent. Source edits in its workspace are bind-mounted at `/testbed`;
the prompt gives a fixed `docker exec` prefix and the image's explicit testbed
Python interpreter for public checks.

## Configuration and lifecycle

Prepare the official images separately, validate the official base/reference
controls, and record their immutable repository digests. The helper never pulls
or builds an image implicitly. On this managed host, sequential image handling
is necessary because Docker's `vfs` driver can consume roughly 20 GB per task
image; do not start concurrent downloads without checking resources.

The configuration covers exactly the frozen task IDs:

```json
{
  "schema_version": 1,
  "mode": "official_image_development_tools",
  "tasks": {
    "sympy__sympy-17139": {
      "image": "swebench/sweb.eval.x86_64.sympy_1776_sympy-17139@sha256:9a8111742e0548816d920a27ba259ebde7647f4e46e7522c61647990dd35713c",
      "probe_argv": [
        "/opt/miniconda3/envs/testbed/bin/python",
        "-c",
        "import sympy; assert sympy.__file__.startswith('/testbed/'); print(sympy.__version__)"
      ],
      "probe_timeout_seconds": 60
    }
  }
}
```

This one-task example does not cover the twelve-task panel. Use appropriate
**public** import or test commands for every selected task; do not supply the
private evaluator script, hidden tests, gold patches, credentials or environment
dumps as probes. A passing import check only validates that import, not the
entire public test suite. Some compiled projects need their prescribed build
step inside a prepared source tree; mounting a fresh checkout can hide compiled
extensions originally built in the image. A failed import must remain a failed
readiness check until the proper public setup is supplied.

The lifecycle API is:

```python
from ttgl.worker import ToolContainer, assert_dependency_ready

with ToolContainer(workspace, task, entry, assignment_id) as environment:
    report = environment.probe()
    assert_dependency_ready(report, task, workspace, entry)
    # Persist report before any model work. Append environment.instructions()
    # to the task prompt; preserve it across controller resumes.
```

Task dictionaries use the standard `instance_id` and exact `base_commit`.
An initial checkout must be clean. `allow_dirty=True` is reserved for an already
recorded, safely resumed assignment; it must not make an unknown workspace into
a fresh trial. The probe hashes tracked changes and untracked files before and
after execution, including already-modified files, and refuses readiness if it
changes source state. Generated ignored caches do not affect this check.

Container names derive from the assignment identity and remain stable across
safe resumes. Actual container IDs, image IDs, image digests, probe command,
output hashes and exit status are recorded separately. A failed probe never
becomes a passing model result. The lifecycle removes only a container whose
task-owner label matches; it refuses destructive cleanup of an unknown owner.
Timeouts or daemon errors preserve the uncertain identity for reconciliation.

## What the boundary establishes

The container receives only the explicit task-checkout bind mount. It has no
network, no added capabilities, a no-new-privileges setting, bounded processes,
two CPUs and four GiB of memory. It runs as the host user's numeric UID/GID.
No Codex credentials, model endpoint configuration or Docker socket is mounted
inside it. Docker's existing registry/proxy configuration is preserved. With
networking disabled and dependencies already installed, the probe needs no
session CA or Internet download. If a later setup genuinely needs network access,
use the supported cloud proxy/CA workflow separately; do not loosen this helper.

This is explicitly a **development dependency environment**, not hardened
isolation for the complete experiment:

- Codex still runs on the host, where read access to other files may exist.
- Codex's own sandbox must separately demonstrate that it can execute the
  intended container test command. The helper cannot prove that a successful
  orchestrator-side Docker command is permitted to the model's tool process.
- Docker socket access can control the host daemon; prompt restrictions do not
  transform it into a narrow, hardened tool permission.
- Keeping evaluation files outside the bind mount is useful, but does not make
  them inaccessible to the host agent.

Accordingly the report has `dependency_ready` plus separate false fields for
`controller_docker_access_verified`, `host_read_isolation_verified`, and
`confirmatory_study_ready`. Do not rename a passing dependency probe as a passed
isolation check. A confirmatory study needs an independently isolated model/tool
runtime with only its assigned repository and public context. Supported existing
environment/harness mechanisms should provide that boundary on the next host.

The native Codex read-only-state blocker remains separate. No dependency helper
can grant model access or billing telemetry by itself. Its software tests and
any public-image smoke checks are infrastructure evidence, not Luna/Sol results.
