"""Fixed public contracts, known-good controls, and host-only check vectors."""


def specifications():
    yield from _historical_tasks()
    yield from _optimization_tasks()
    yield from _heldout_tasks()


def _historical_tasks():
    yield (
        "apportion-cents", "historical", "Allocate signed amounts exactly", "apportion",
        """
        Repair **apportion(amount, weights)**. Allocate integer cents in proportion
        to a list of nonnegative integer weights. Begin with the whole-cent floor
        of each share of the absolute amount. Give remaining cents to the largest
        fractional remainders, resolving ties by input order. Restore the amount's
        sign after allocating cents. Empty weights return an empty list. All-zero
        weights return a matching list of zeroes, including for nonzero amounts.
        Inputs may be larger than a double can represent exactly.
        """,
        """
        def apportion(amount, weights):
            if not sum(weights):
                return [0] * len(weights)
            return [round(amount * weight / sum(weights)) for weight in weights]
        """,
        """
        def apportion(amount, weights):
            total = sum(weights)
            if not total:
                return [0] * len(weights)
            shares = [divmod(abs(amount) * weight, total) for weight in weights]
            allocations = [whole for whole, _ in shares]
            order = sorted(range(len(weights)), key=lambda i: (-shares[i][1], i))
            for index in order[:abs(amount) - sum(allocations)]:
                allocations[index] += 1
            return [-value if amount < 0 else value for value in allocations]
        """,
        [([12, [1, 3]], [3, 9])],
        [
            ([5, [1, 1, 1]], [2, 2, 1]),
            ([-7, [0, 2, 1, 2]], [0, -3, -1, -3]),
            ([17, [0, 0, 0]], [0, 0, 0]),
            ([4, []], []),
            ([9007199254740997, [1, 1]], [4503599627370499, 4503599627370498]),
            ([0, [2, 1]], [0, 0]),
        ],
    )

    yield (
        "paint-region", "historical", "Paint a connected region of a ragged grid", "paint",
        """
        Repair **paint(rows, start, replacement, diagonal)**. Return a new list of
        rows, recoloring exactly the region reachable from the zero-indexed
        [row, column] start through cells matching the start's original color.
        Cells are string labels or null. Null is a hole and never traversable.
        Use edge neighbors when diagonal is false and both edge and corner
        neighbors when diagonal is true. Missing columns in ragged rows are
        holes. An out-of-bounds or hole start returns unchanged values. The
        replacement is always a string. Replacing with the same color leaves
        values unchanged. The inputs can contain regions larger than 1,000 cells.
        """,
        """
        def paint(rows, start, replacement, diagonal):
            row, column = start
            original = rows[row][column]
            return [[replacement if cell == original else cell for cell in line]
                    for line in rows]
        """,
        """
        def paint(rows, start, replacement, diagonal):
            result = [list(row) for row in rows]
            def inside(row, column):
                return 0 <= row < len(rows) and 0 <= column < len(rows[row])
            row, column = start
            if not inside(row, column):
                return result
            original = rows[row][column]
            if original is None or original == replacement:
                return result
            pending = [(row, column)]
            while pending:
                row, column = pending.pop()
                if not inside(row, column) or result[row][column] != original:
                    continue
                result[row][column] = replacement
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if (dx or dy) and (diagonal or not (dx and dy)):
                            pending.append((row + dy, column + dx))
            return result
        """,
        [([[["r", "r", "b"]], [0, 0], "x", False], [["x", "x", "b"]])],
        [
            ([[["a", None, "a"], ["a"], [], ["a"]], [0, 0], "z", False],
             [["z", None, "a"], ["z"], [], ["a"]]),
            ([[["r", "b"], ["b", "r"]], [0, 0], "x", False], [["x", "b"], ["b", "r"]]),
            ([[["r", "b"], ["b", "r"]], [0, 0], "x", True], [["x", "b"], ["b", "x"]]),
            ([[[None, "b"]], [0, 0], "x", False], [[None, "b"]]),
            ([[["r"], [], ["b"]], [-1, 0], "x", True], [["r"], [], ["b"]]),
            ([[["r"] * 1501], [0, 1], "x", False], [["x"] * 1501]),
            ([[["a", "a"]], [0, 0], "a", False], [["a", "a"]]),
        ],
    )

    yield (
        "alias-collisions", "historical", "Report normalized display-name collisions",
        "alias_collisions",
        """
        Repair **alias_collisions(names)**. Each name is a Unicode string. Normalize
        it using NFKC, then casefold it, then collapse runs of Python whitespace to
        one ASCII space and trim surrounding space. Ignore empty normalized names.
        Return only collisions as a list of index lists. Include every index in
        each group in ascending order, and order groups by their first index.
        """,
        """
        def alias_collisions(names):
            groups = {}
            for index, name in enumerate(names):
                groups.setdefault(name.lower().strip(), []).append(index)
            return [group for group in groups.values() if len(group) > 1]
        """,
        """
        from unicodedata import normalize

        def alias_collisions(names):
            groups = {}
            for index, name in enumerate(names):
                key = " ".join(normalize("NFKC", name).casefold().split())
                if key:
                    groups.setdefault(key, []).append(index)
            return [indexes for indexes in groups.values() if len(indexes) > 1]
        """,
        [([["Blue", "amber", " blue "]], [[0, 2]])],
        [
            ([["Straße", "STRASSE", "ς", "Σ", "other"]], [[0, 1], [2, 3]]),
            ([["ＭＯＯＮ", " moon ", "Café", "Cafe\u0301"]], [[0, 1], [2, 3]]),
            ([["", " \t", "A\u00a0\u2003B", " a b ", "\n"]], [[2, 3]]),
            ([["beta", "alpha", "Gamma", "ALPHA", "Beta", "BETA"]], [[0, 4, 5], [1, 3]]),
            ([["only", "plain"]], []),
        ],
    )

    yield (
        "order-versions", "historical", "Order tagged release versions", "order_versions",
        """
        Repair **order_versions(versions)**. A version is MAJOR.MINOR.PATCH with
        optional hyphen-prefixed dot-separated prerelease identifiers and
        plus-prefixed dot-separated build identifiers. Inputs are valid strings
        containing only ASCII in these components. Ignore build metadata for
        precedence. Compare the three core fields as nonnegative integers. A
        final release follows any prerelease of the same core. Compare prerelease
        identifiers left to right, treating all-digit identifiers as integers
        that precede any nonnumeric identifier. Nonnumeric identifiers compare
        in ASCII order. When one prerelease is an exact prefix of the other,
        the shorter comes first. Equal precedence keeps original input order.
        Return the original strings, sorted from lowest precedence to highest.
        """,
        """
        def order_versions(versions):
            return sorted(versions)
        """,
        """
        def order_versions(versions):
            def precedence(version):
                core, marker, prerelease = version.partition("+")[0].partition("-")
                core_numbers = tuple(map(int, core.split(".")))
                identifiers = tuple((0, int(part)) if part.isdigit() else (1, part)
                                    for part in prerelease.split(".")) if marker else ()
                return core_numbers, not marker, identifiers
            return sorted(versions, key=precedence)
        """,
        [([["2.0.1", "1.3.1", "1.2.0"]], ["1.2.0", "1.3.1", "2.0.1"])],
        [
            ([["9.10.0", "10.0.0", "9.2.0"]], ["9.2.0", "9.10.0", "10.0.0"]),
            ([["1.0.0", "1.0.0-rc.10", "1.0.0-rc.2", "1.0.0-rc"]],
             ["1.0.0-rc", "1.0.0-rc.2", "1.0.0-rc.10", "1.0.0"]),
            ([["1.0.0+z", "1.0.0+a", "1.0.0+1"]], ["1.0.0+z", "1.0.0+a", "1.0.0+1"]),
            ([["0.1.0-z", "0.1.0-A", "0.1.0-9", "0.1.0-2.0", "0.1.0-2"]],
             ["0.1.0-2", "0.1.0-2.0", "0.1.0-9", "0.1.0-A", "0.1.0-z"]),
            ([[]], []),
        ],
    )


def _optimization_tasks():
    yield (
        "split-pipeline", "optimization", "Parse a command pipeline without executing it", "split_pipeline",
        r"""
        Repair **split_pipeline(text)**. Return pipeline stages as a list of lists
        of words. An unquoted pipe separates stages and unquoted whitespace
        separates words. Single and double quotes remove delimiters and preserve
        their contents. Backslash quotes exactly the next character outside a
        single-quoted section. Adjacent quoted and unquoted parts form one word.
        Empty quotes are a word. If a stage is empty, a quote is unclosed, or an
        escape is unfinished, return null. A whitespace-only string returns [].
        """,
        """
        def split_pipeline(text):
            return [stage.split() for stage in text.split("|")] if text.strip() else []
        """,
        r"""
        def split_pipeline(text):
            stages, stage, characters = [], [], []
            quote = None
            escaped = started = False

            def finish_word():
                nonlocal started
                if started:
                    stage.append("".join(characters))
                    characters.clear()
                    started = False

            for char in text:
                if escaped:
                    characters.append(char)
                    escaped = False
                elif char == chr(92) and quote != "'":
                    started = escaped = True
                elif quote:
                    if char == quote:
                        quote = None
                    else:
                        characters.append(char)
                elif char in "'\"":
                    started, quote = True, char
                elif char == "|":
                    finish_word()
                    if not stage:
                        return None
                    stages.append(stage)
                    stage = []
                elif char.isspace():
                    finish_word()
                else:
                    started = True
                    characters.append(char)
            if quote or escaped:
                return None
            finish_word()
            if stage:
                stages.append(stage)
            elif stages:
                return None
            return stages
        """,
        [(["go left | count"], [["go", "left"], ["count"]])],
        [
            (['pie"pe |" x\\ y | log ""'], [["piepe |", "x y"], ["log", ""]]),
            (["print 'a\\b' | end"], [["print", "a\\b"], ["end"]]),
            (["| left"], None),
            (["go |   "], None),
            (["cmd \\"], None),
            (['cmd "a'], None),
            (["   "], []),
            (["one \\| two"], [["one", "|", "two"]]),
        ],
    )
    yield (
        "compatible-batches", "optimization", "Pack jobs into runs without changing priority", "pack_jobs",
        """
        Repair **pack_jobs(jobs, capacity)**. Each job has a unique string "id",
        a nonnegative integer "size", and a string "group". Capacity is positive.
        Iterate in input order. A job larger than capacity is rejected. Put each
        remaining job into the earliest-created batch that has sufficient remaining
        capacity and does not already contain a job of its group. If no batch
        qualifies, create a batch. Return {"batches": [[ids], ...], "rejected": [ids]}
        and keep insertion order within each list. Leave input jobs unchanged.
        """,
        """
        def pack_jobs(jobs, capacity):
            batches = []
            for job in jobs:
                if job["size"] <= capacity:
                    batches.append([job["id"]])
            return {"batches": batches, "rejected": []}
        """,
        """
        def pack_jobs(jobs, capacity):
            batches, rejected = [], []
            for job in jobs:
                size, group = job["size"], job["group"]
                if size > capacity:
                    rejected.append(job["id"])
                    continue
                for batch in batches:
                    remaining, groups, ids = batch
                    if size <= remaining and group not in groups:
                        batch[0] -= size
                        groups.add(group)
                        ids.append(job["id"])
                        break
                else:
                    batches.append([capacity - size, {group}, [job["id"]]])
            return {"batches": [batch[2] for batch in batches], "rejected": rejected}
        """,
        [([[_job("a", 3, "x"), _job("b", 3, "y")], 3],
          {"batches": [["a"], ["b"]], "rejected": []})],
        [
            ([[_job("a", 7, "x"), _job("b", 3, "x"), _job("c", 2, "y"),
               _job("d", 6, "z"), _job("e", 4, "w")], 10],
             {"batches": [["a", "c"], ["b", "d"], ["e"]], "rejected": []}),
            ([[_job("q", 8, "x"), _job("a", 4, "x"), _job("z", 0, "y")], 4],
             {"batches": [["a", "z"]], "rejected": ["q"]}),
            ([[_job("a", 0, "x"), _job("b", 0, "x"), _job("c", 0, "y")], 1],
             {"batches": [["a", "c"], ["b"]], "rejected": []}),
            ([[_job("a", 1, "z"), _job("b", 3, "x"), _job("c", 2, "y"),
               _job("d", 1, "q"), _job("e", 2, "y")], 3],
             {"batches": [["a", "c"], ["b"], ["d", "e"]], "rejected": []}),
            ([[], 1], {"batches": [], "rejected": []}),
        ],
    )
    yield (
        "rank-events", "optimization", "Select canonical events from synchronized feeds", "rank_events",
        """
        Repair **rank_events(feeds, start, stop)**. Each input feed is a list of
        dictionaries containing string "id", integer "ts", nonnegative integer
        "revision", and any additional JSON fields. Choose one event for each id
        across all feeds: greatest revision wins, then greatest timestamp, then
        earliest feed and earliest position. After choosing winners, keep those
        whose timestamp is in [start, stop). Return the original event contents
        sorted by increasing timestamp and then id. If start >= stop return [].
        """,
        """
        def rank_events(feeds, start, stop):
            return sorted((event for feed in feeds for event in feed
                           if start <= event["ts"] < stop), key=lambda event: event["ts"])
        """,
        """
        def rank_events(feeds, start, stop):
            winners = {}
            for feed in feeds:
                for event in feed:
                    previous = winners.get(event["id"])
                    if previous is None or (event["revision"], event["ts"]) > (previous["revision"], previous["ts"]):
                        winners[event["id"]] = event
            return sorted((event for event in winners.values() if start <= event["ts"] < stop),
                          key=lambda event: (event["ts"], event["id"]))
        """,
        [([[[_event("a", 1, 0), _event("b", 2, 0)]], 1, 3],
          [_event("a", 1, 0), _event("b", 2, 0)])],
        [
            ([[[_event("a", 1, 0), _event("b", 2, 0)], [_event("a", 9, 1)]], 1, 5],
             [_event("b", 2, 0)]),
            ([[[_event("a", 4, 2)], [_event("a", 1, 3)]], 0, 5], [_event("a", 1, 3)]),
            ([[[_event("a", 1, 0, "first"), _event("a", 1, 0, "second")],
               [_event("a", 1, 0, "third"), _event("b", 0, 0)]], 0, 2],
             [_event("b", 0, 0), _event("a", 1, 0, "first")]),
            ([[[_event("b", 2, 0), _event("a", 2, 0), _event("c", 3, 0)]], 2, 3],
             [_event("a", 2, 0), _event("b", 2, 0)]),
            ([[[_event("a", 1, 0), _event("a", 4, 0)]], 0, 8], [_event("a", 4, 0)]),
            ([[[_event("a", 1, 0)]], 5, 4], []),
        ],
    )


def _heldout_tasks():
    yield (
        "overlay-bundles", "heldout", "Apply ordered configuration overlays", "overlay",
        """
        Repair **overlay(base, layers)**. Starting with the JSON object base,
        apply each object in layers in order and return the final object. A null
        value in a layer removes that key if present. A nested object recursively
        applies these same rules starting with the existing nested object if it
        is an object, otherwise starting empty. Lists and other values replace
        the key wholesale. Nulls inside lists or already present in base must
        remain unless that key is explicitly changed. An empty nested object
        creates an empty object when missing and leaves an existing object
        alone. Keys and values should never be taken from an input by mutable
        reference. Leave all inputs unchanged.
        """,
        """
        def overlay(base, layers):
            result = base.copy()
            for layer in layers:
                result.update(layer)
            return result
        """,
        """
        from copy import deepcopy

        def overlay(base, layers):
            result = deepcopy(base)
            def apply(target, patch):
                for key, value in patch.items():
                    if value is None:
                        target.pop(key, None)
                    elif isinstance(value, dict):
                        nested = target.get(key)
                        if not isinstance(nested, dict):
                            nested = target[key] = {}
                        apply(nested, value)
                    else:
                        target[key] = deepcopy(value)
            for layer in layers:
                apply(result, layer)
            return result
        """,
        [([{"a": 1}, [{"b": 2}]], {"a": 1, "b": 2})],
        [
            ([{"a": {"b": 1, "c": 2}, "z": None}, [{"a": {"b": None, "d": [None]}}]],
             {"a": {"c": 2, "d": [None]}, "z": None}),
            ([{"x": [1]}, [{"x": {"a": 1}}, {"x": None}, {"x": {"b": 2}}]], {"x": {"b": 2}}),
            ([{"a": {"previous": 8}}, [{"a": {}, "b": {}, "missing": None}]],
             {"a": {"previous": 8}, "b": {}}),
            ([{}, [{"a": {"b": None, "c": {"d": None}}}]], {"a": {"c": {}}}),
            ([{"x": {"a": 2}}, [{"x": [{"a": None}, None]}]], {"x": [{"a": None}, None]}),
            ([{"a": [1, 2], "b": None}, []], {"a": [1, 2], "b": None}),
        ],
    )
    yield (
        "coalesce-samples", "heldout", "Build contiguous runs from telemetry samples", "coalesce",
        """
        Repair **coalesce(samples, max_gap)**. A sample is a pair [tick, state].
        Ticks are integers in any input order, state is a string or null, and
        max_gap is a nonnegative integer. Resolve duplicate ticks by keeping
        their last state in input order, then process ticks in ascending order.
        An observed null state terminates the current run and is excluded.
        Two consecutive non-null observations belong to one run only if their
        states match and their tick difference is at most max_gap. Return
        [first_tick, last_tick, state] for each run in ascending order. Keep
        runs with one sample. Do not extend to unobserved endpoints.
        """,
        """
        def coalesce(samples, max_gap):
            result = []
            for tick, state in samples:
                if state is not None:
                    result.append([tick, tick, state])
            return result
        """,
        """
        def coalesce(samples, max_gap):
            runs = []
            active = None
            for tick, state in sorted(dict(samples).items()):
                if state is None:
                    active = None
                elif active is not None and state == active[2] and tick - active[1] <= max_gap:
                    active[1] = tick
                else:
                    active = [tick, tick, state]
                    runs.append(active)
            return runs
        """,
        [([[[0, "ready"], [5, "idle"]], 7], [[0, 0, "ready"], [5, 5, "idle"]])],
        [
            ([[[8, "a"], [2, "a"], [6, "b"], [6, "a"], [3, None], [5, "a"]], 3],
             [[2, 2, "a"], [5, 8, "a"]]),
            ([[[0, "x"], [2, "x"], [4, "x"], [9, "x"]], 2], [[0, 4, "x"], [9, 9, "x"]]),
            ([[[0, "x"], [1, "x"], [1, None], [2, "x"]], 10], [[0, 0, "x"], [2, 2, "x"]]),
            ([[[-2, "x"], [-1, "x"], [4, "x"], [4, "y"]], 0],
             [[-2, -2, "x"], [-1, -1, "x"], [4, 4, "y"]]),
            ([[[0, None], [1, None]], 0], []),
            ([[], 8], []),
        ],
    )
    yield (
        "flatten-rules", "heldout", "Resolve defaults through an inheritance chain", "resolve_rules",
        """
        Repair **resolve_rules(rules, key)**. Each named rule is a JSON object
        optionally containing "parent", the name of one other rule, and
        "values", a flat object of JSON values. Follow parents to the root.
        Return values merged root-first, with descendants overriding keys.
        A null value in a rule's "values" deletes the key inherited from
        ancestors. A later descendant can restore it. Missing or null parent
        ends the chain. Return null if the requested rule or any ancestor is
        missing, or if the chain has a cycle. Rules outside the chain are
        irrelevant. Values do not merge recursively. Chains may be very deep.
        """,
        """
        def resolve_rules(rules, key):
            return rules.get(key, {}).get("values", {}).copy()
        """,
        """
        def resolve_rules(rules, key):
            seen, chain = set(), []
            while key is not None:
                if key in seen or key not in rules:
                    return None
                seen.add(key)
                rule = rules[key]
                chain.append(rule.get("values", {}))
                key = rule.get("parent")
            result = {}
            for values in reversed(chain):
                for name, value in values.items():
                    if value is None:
                        result.pop(name, None)
                    else:
                        result[name] = value
            return result
        """,
        [([{"base": {"values": {"x": 4}}}, "base"], {"x": 4})],
        [
            ([{"a": {"values": {"r": 1, "x": 2}},
               "b": {"parent": "a", "values": {"r": None, "x": {"a": 3}}},
               "c": {"parent": "b", "values": {"r": 7, "x": {"b": 8}}}}, "c"],
             {"r": 7, "x": {"b": 8}}),
            ([{"a": {"parent": "b"}, "b": {"parent": "a"}}, "a"], None),
            ([{"a": {"parent": "absent"}}, "a"], None),
            ([{"a": {"parent": "a"}, "b": {}}, "b"], {}),
            ([{}, "a"], None),
            ([_rule_chain(1100), "1099"], {"x": 11, "last": 12}),
        ],
    )
    yield (
        "common-prefix-window", "heldout", "Find a shortest covering token window", "covering_window",
        """
        Repair **covering_window(tokens, required)**. Each input is a list of
        strings. Return [start, end] using zero-based start and exclusive end of
        the shortest contiguous slice of tokens containing every requested token
        at least as many times as it appears in required. Among equal-length
        slices choose smallest start. Return [0, 0] for no required tokens,
        and null if no slice qualifies. Match token strings exactly. Lengths
        may be large, so avoid enumerating all possible slices.
        """,
        """
        def covering_window(tokens, required):
            if all(token in tokens for token in required):
                return [0, len(tokens)]
            return None
        """,
        """
        from collections import Counter

        def covering_window(tokens, required):
            need = Counter(required)
            if not need:
                return [0, 0]
            missing = len(required)
            start = 0
            best = None
            for end, token in enumerate(tokens, 1):
                if need[token] > 0:
                    missing -= 1
                need[token] -= 1
                while not missing:
                    if best is None or end - start < best[1] - best[0]:
                        best = [start, end]
                    left = tokens[start]
                    need[left] += 1
                    missing += need[left] > 0
                    start += 1
            return best
        """,
        [([["green", "blue"], ["green", "blue"]], [0, 2])],
        [
            ([["x", "a", "b", "a", "c", "a", "b"], ["a", "a", "b"]], [1, 4]),
            ([["z", "z", "x", "z"], ["z", "x"]], [1, 3]),
            ([["a", "b", "c"], ["b", "b"]], None),
            ([["x"], []], [0, 0]),
            ([["A", "A", "a", "", "a"], ["a", "", "a"]], [2, 5]),
            ([["a"] * 16000 + ["b"] * 12000, ["a", "b", "b"]], [15999, 16002]),
        ],
    )


def _job(identity, size, group):
    return {"id": identity, "size": size, "group": group}


def _event(identity, timestamp, revision, payload=None):
    return {"id": identity, "ts": timestamp, "revision": revision, "payload": payload}


def _rule_chain(length):
    rules = {"0": {"values": {"x": 11}}}
    rules.update({str(index): {"parent": str(index - 1)} for index in range(1, length)})
    rules[str(length - 1)]["values"] = {"last": 12}
    return rules
