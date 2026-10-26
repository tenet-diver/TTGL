# Live forced-dialogue mechanism check

Controller: `gpt-6-luna`, medium, fresh context.
Expert: `gpt-6.1-sol`, medium, fresh context initially; the same thread receives the follow-up.
Expert thread: `/root/dialogue_smoke_controller/custom_repr_expert`.
Controller thread: `/root/dialogue_smoke_controller`.

This is a separately planned engineering check after the four optional-dialogue
controllers reported zero consultations. A clarification was required by the
check. It is not part of the four-arm performance matrix or evidence of savings.
The following are visible messages reported by the controller, not private
reasoning. No token or dollar usage was exposed.

## Controller → expert, first request

Selected context: The task is to make PySnooper's snoop decorator accept
custom_repr either as one (condition, formatter) pair or an ordered sequence of
such pairs. Conditions can be types (match instances) or predicates; first
matching formatter handles local value display, with default repr otherwise.
Preserve existing tracing API/default behavior, supported Python compatibility,
and avoid runtime dependencies. Inspection found Tracer.__init__ currently
accepts output, watch, watch_explode, depth, prefix, overwrite, thread_info only;
get_local_reprs(frame, watch=()) uses utils.get_shortish_repr(value) for all frame
locals and watched values. Tracer.trace calls that helper for local snapshots;
variable expansion formatting is in variables.py. We need a small source-only
fix plus focused tests. Explicitly do not use tools, filesystem, network, or
other agents. First respond with exactly ONE clarification question about
needed context or constraints, and do not give a solution yet.

## Expert → controller, clarification

Should custom_repr also apply to watched expressions and expanded values, or
only ordinary frame locals?

## Controller → same expert, second request

Investigation shows watched expressions and exploded values are produced in
variables.py by BaseVariable.items/CommonVariable._items and are currently
independently rendered with utils.get_shortish_repr; the task specifically says
“when rendering local values,” so keep custom_repr scoped to ordinary frame
locals for this repair and preserve watched/exploded behavior. Please give your
final proposal now.

## Expert → controller, proposal

Add `custom_repr=()` as the final `Tracer.__init__` parameter, preserving
existing positional arguments.

Normalize it once into an ordered tuple of `(condition, formatter)` pairs.
Recognize a single pair when both elements are callable; types qualify as
callable conditions. A two-pair sequence remains unambiguous because its
elements are pairs.

For ordinary frame locals:

1. Evaluate each condition in order: `isinstance(value, condition)` for types,
   otherwise `condition(value)`.
2. Use the first matching formatter.
3. Fall back to `repr` when nothing matches.
4. Pass the selected representation through the existing shortening and
   error-handling logic.

Thread the normalized rules through `get_local_reprs`; keep watched expressions
and expanded values on their existing rendering path. If necessary, extend
`utils.get_shortish_repr` with an optional trailing `repr_func=repr` parameter so
custom formatting retains its existing truncation and exception behavior.

Focused tests should cover:

- A single type pair, including subclass instances.
- A single predicate pair.
- Ordered multiple pairs with first-match precedence.
- Unmatched values and omitted `custom_repr` preserving defaults.
- Long custom output preserving truncation.
- Watched and expanded values retaining their existing formatting.

Use syntax compatible with the repository’s supported Python versions and add
no dependencies.

## Integration and independent check

The controller changed `pysnooper/tracer.py`, `pysnooper/utils.py` and added a new
test file. It reported 32 public tests passing. The independent fixed regression
module passed all 30 selected tests, with no artifact-policy violation. See the
corrected grading report and the retained note about the first collector's
relative JUnit path. The model was not rerun for that collector correction.
