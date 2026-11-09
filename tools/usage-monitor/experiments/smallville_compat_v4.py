"""Explicit structured triple format for modern models; versioned prompt adaptation.

Original body is retained, but this is not original-prompt parity. No retries or
invented tuples on refusal/malformed output. Ranking/reflection evidence unchanged.
"""
import json
from smallville_compat_v3 import CompatibleMemoryV3
from smallville_memory import render


def triple_prompt(description, name):
    if '(' in description:
        description = description.split('(')[-1].split(')')[0]
    original = render('v2/generate_event_triple_v1.txt', [name, description, name])
    return (original + '\n\nThe preceding prompt ends with an unfinished example tuple. '
            'Perform structured extraction from the following explicit data, rather than '
            'requesting clarification about that unfinished format. Return ONLY a JSON '
            'array of three nonempty strings: [subject, predicate, object]. Use the supplied '
            'agent name as subject and represent the supplied statement faithfully; do not '
            'add facts.\n' + json.dumps(dict(agent=name, statement=description)))


def parse_triple(answer, name):
    raw = json.loads(answer)
    if (not isinstance(raw, list) or len(raw) != 3 or
            any(not isinstance(x, str) or not x.strip() for x in raw) or raw[0] != name):
        raise ValueError('Invalid structured triple')
    return tuple(raw)


class CompatibleMemoryV4(CompatibleMemoryV3):
    def _triple(self, description, persona):
        answer = self.call(triple_prompt(description, persona.name), 'reflection_triple_v4')
        return parse_triple(answer, persona.name), None
