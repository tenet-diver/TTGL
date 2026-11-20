"""Two fresh dependent stdlib tasks for the decision-history study."""
from dataclasses import dataclass
from textwrap import dedent

from .sim_ablation.benchmark import Task


@dataclass(frozen=True)
class Handoff:
    name: str
    predecessor: Task
    continuation: Task


def _text(value):
    return dedent(value).strip() + "\n"


def _task(identity, function, spec, starter, reference, public, private):
    tests = [f"from solution import {function}", "import unittest", "",
             "class Checks(unittest.TestCase):", "    def test_examples(self):"]
    for argument, expected in public:
        tests.append(f"        self.assertEqual({function}({argument!r}), {expected!r})")
    return Task(identity, "development", identity, _text(spec), function, _text(starter), "\n".join(tests) + "\n",
                tuple(([argument], expected) for argument, expected in private), _text(reference))


SEATS_SPEC = """
    Implement `allocated(events)`, returning the active seat names in their activation
    order. The input is a list of records. At this checkpoint the recognized records are
    [action, name] with action exactly 'book' or 'cancel'. Normalize each name with
    strip then casefold; ignore blank or nonstring names. Ignore malformed records
    and unknown actions. A duplicate booking does not move a seat. Canceling an
    absent seat does nothing. Canceling then booking again appends the seat.
    Do not mutate the input.
"""
SEATS_START = """
    def allocated(events):
        active = []
        for event in events:
            if not isinstance(event, list) or len(event) != 2:
                continue
            action, name = event
            if not isinstance(name, str) or not (name := name.strip().casefold()):
                continue
            if action == 'book':
                active.append(name)
            elif action == 'cancel' and name in active:
                active.remove(name)
        return active
"""
SEATS_BASE = _text(SEATS_START).replace("if action == 'book':", "if action == 'book' and name not in active:")
SEATS_TARGET = SEATS_BASE.replace("        if not isinstance(event, list) or len(event) != 2:", """        if isinstance(event, list) and len(event) == 3 and event[0] == 'rename':
            old, new = event[1:]
            if isinstance(old, str) and isinstance(new, str):
                old, new = old.strip().casefold(), new.strip().casefold()
                if new and old in active and new not in active:
                    active[active.index(old)] = new
            continue
        if not isinstance(event, list) or len(event) != 2:""")

FLAGS_SPEC = """
    Implement `resolve(layers)`, returning the effective flag mapping. Each layer
    is an ordered list of [key, value] entries. Apply layers and entries in order.
    Normalize string keys using strip then casefold and ignore empty names or the
    reserved name '*'. A None value deletes a key. Keep all other JSON values,
    including false, zero and the empty string. Ignore malformed layers and
    entries. Do not mutate the input.
"""
FLAGS_START = """
    def resolve(layers):
        result = {}
        for layer in layers:
            if not isinstance(layer, list):
                continue
            for entry in layer:
                if not isinstance(entry, list) or len(entry) != 2 or not isinstance(entry[0], str):
                    continue
                raw, value = entry
                key = raw.strip().casefold()
                if not key or key == '*':
                    continue
                if not value:
                    result.pop(key, None)
                else:
                    result[key] = value
        return result
"""
FLAGS_BASE = _text(FLAGS_START).replace("if not value:", "if value is None:")
FLAGS_TARGET = FLAGS_BASE.replace("            if not key or key == '*':", """            if key == '*' and value is None:
                result.clear()
                continue
            if not key or key == '*':""")

def _layer_cases(rows):
    return [([[[key, value] for key, value in layer.items()] if isinstance(layer, dict) else layer for layer in layers], expected)
            for layers, expected in rows]


def tasks():
    seats = Handoff("seats", _task("seat-activation", "allocated", SEATS_SPEC, SEATS_START, SEATS_BASE, [
        ([["book", " A "], ["book", "B"], ["book", "a"]], ["a", "b"]),
        ([["book", "a"], ["book", "b"], ["cancel", "a"], ["book", "A"]], ["b", "a"]),
    ], [
        ([], []), ([["book", " Z "], ["book", "z"]], ["z"]),
        ([["cancel", "m"], ["book", "r"], ["book", "x"], ["cancel", "r"], ["book", "R"]], ["x", "r"]),
        ([42, ["book", " "], ["book", 4], ["bad", "y"], ["BOOK", "q"], ["book", "s"]], ["s"]),
    ]), _task("seat-rename", "allocated", """
        Add records ['rename', old, new]. Normalize both names using the earlier
        rules. When old is active and new is nonblank and free, replace old with
        new in the same position. Ignore renames with an absent old name, a
        destination already active, or a malformed source or destination.
        Preserve checkpoint 1 behavior for earlier records.
    """, SEATS_BASE, SEATS_TARGET, [
        ([["book", "a"], ["book", "b"], ["rename", "A", " C "]], ["c", "b"]),
        ([["book", "a"], ["book", "b"], ["rename", "a", "b"]], ["a", "b"]),
    ], [
        ([["book", "r"], ["book", "s"], ["book", "t"], ["rename", "s", "u"]], ["r", "u", "t"]),
        ([["book", "x"], ["rename", "x", "x"], ["rename", "x", 1], ["rename", "y", "z"]], ["x"]),
        ([["book", "b"], ["rename", "b", "C"], ["cancel", "c"], ["book", "b"]], ["b"]),
        ([["book", "ß"], ["rename", "SS", " Q "], ["book", "q"]], ["q"]),
    ]))
    flags = Handoff("flags", _task("layered-flags", "resolve", FLAGS_SPEC, FLAGS_START, FLAGS_BASE, _layer_cases([
        ([{"Enabled": True, "count": 2}, {" enabled ": False, "Count": 0}], {"enabled": False, "count": 0}),
        ([{"name": "a"}, {" Name ": None, "fallback": ""}], {"fallback": ""}),
    ]), _layer_cases([
        ([{"q": False, "r": 0, "s": ""}], {"q": False, "r": 0, "s": ""}),
        ([{"q": 5}, [], {" Q ": None, " R ": []}], {"r": []}),
        ([{"A": 1, "a": 2, " ": 3, "*": True}], {"a": 2}),
        ([{"x": None}, "wrong", {"X": False}], {"x": False}),
    ])), _task("layer-reset", "resolve", """
        Add a reset directive. A normalized key '*' with value None clears all
        currently effective keys immediately, including keys set earlier in the
        same layer. Continue applying later entries in order. A '*' entry with
        any other value is still ignored. Preserve earlier behavior otherwise.
    """, FLAGS_BASE, FLAGS_TARGET, _layer_cases([
        ([{"a": 1}, {"b": 2, " * ": None, "c": False}], {"c": False}),
        ([{"x": 7}, {"*": False, "y": 0}], {"x": 7, "y": 0}),
    ]), _layer_cases([
        ([{"x": 1}, {"z": "", "*": None, "n": 0}, {"p": False}], {"n": 0, "p": False}),
        ([{"x": 1}, {"*": None}, {"X": None}], {}),
        ([{"a": 1, " *": None, "b": 2, "* ": None, "c": ""}], {"c": ""}),
        ([{"*": []}, {" A ": [0], "*": True}], {"a": [0]}),
    ])))
    return (seats, flags)
