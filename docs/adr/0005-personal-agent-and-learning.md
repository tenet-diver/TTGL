# ADR 0005: A personal agent that collaborates and learns

Date: 2026-10-25  
Status: Accepted research direction; cooperative and longitudinal results pending  
Scope: Extends ADR 0004. Portfolio routing is infrastructure for personal capability, rather than the entire product.

## Objective

Democratize useful AI through an affordable, user-controlled personal model that can work locally, obtain expertise from the open model ecosystem and learn from verified experience. Greater independent capability and better collaboration are distinct useful outcomes. Eliminating larger models is not a prerequisite for a valuable personal agent.

## Architecture decision

Use a compact personal controller with an explicit task contract, editable user memory, workspace state and bounded tools. The controller can act locally, consult an expert, delegate a subtask, request critique, verify an artifact, integrate it or request stronger planning. The harness enforces permissions and budgets independently of model output. The external expert need not own all user history or become the long-lived personal identity.

Retain the expert portfolio, but distinguish selecting an expert from controlling the full interaction. Use structured requests and results through maintained model and agent interfaces. Ordinary model weights, private internal reasoning and KV caches are not interchangeable across experts. A bounded request can avoid transferring the controller's full ongoing context; its effectiveness must be measured rather than assumed.

Keep current facts, corrections and preferences in editable memory first. Train adapters or a full student only when repeated verified behavior supports a measurable benefit. Customer artifacts remain associated with compatible base revisions and declared permissions. Reuse maintained agent, memory, training and evaluation components; validate their current interfaces before adoption.

## Learning decision

Collect observable actions, expert requests, permitted context, returned artifacts, verification and integration decisions. Train local coding skills and collaboration skills as separately identified targets. Do not label every action in a successful trajectory optimal, and do not train on a future expert response when predicting an earlier delegation decision.

Use frozen teacher pools and common development exposure streams for causal learning comparisons. Evaluate successive checkpoints on a sealed panel after the learning campaign is frozen. Compare frozen and adapted students with separately frozen or recalibrated policies. Actual interactive collaboration requires fresh continuation runs. Memory updates, router updates and generator training are separate interventions.

## Evaluation decision

The fixed-model cooperation study compares the personal controller plus experts with a large-model agent receiving the same personal information, tools and resource caps. The first controlled contrast uses the same strong expert in both conditions so that adding a better expert is not confused with a benefit of cooperation. Expanded pools and role reversal are additional ablations.

A separate longitudinal study measures standalone local capability, cooperative task success, verified local completion coverage, expert burden and full lifecycle cost across exposure rounds. Lower expert usage supports a claim of independence only when quality is maintained. More effective expert use can support a narrower cooperation claim even if call count does not decline.

Measure technical access through device memory, latency, offline operation, cost and artifact portability. Do not claim universal device support, monotonic learning or societal democratization from a benchmark gain. Existing US$100 Runpod authorization remains unchanged and does not fund the entire new study.

See the [personal controller](../thesis/personal-controller.md), [learning protocol](../thesis/longitudinal-learning.md), [agent-learning evidence](../thesis/agent-learning-evidence.md) and [thesis](../thesis/README.md).
