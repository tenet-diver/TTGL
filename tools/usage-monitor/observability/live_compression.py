"""Tool-result-only transforms for the live Codex request path; stdlib only."""
import hashlib
import json
import time

from progress_output import compact
from vendor.headroom.lossless_compaction import collapse_runs, expand_runs, search_heading, search_unheading, search_dir_heading, search_dir_unheading

POLICIES = ('off', 'progress', 'headroom-lossless')
RAW_MARKER = 'TTGL_RAW_EVIDENCE'


def transform_text(text, policy):
    """Return a smaller presentation, or the exact original. Never touch code/prompts."""
    if len(text) < 1000 or RAW_MARKER in text:
        return text, None
    original = text
    name = None
    reversible = False
    if policy in ('progress', 'headroom-lossless'):
        result = compact(text)
        if result['removed_lines']:
            text = result['output']
            name = 'docker-plain-progress-v1'
    if policy == 'headroom-lossless' and name is None:
        # No ANSI stripping, lossy dropping, code slicing, model inference or telemetry.
        # Only search-shaped rows or recognizable log lines are eligible.
        candidates = []
        if any(':' in line and line.partition(':')[2].partition(':')[0].isdigit() for line in text.splitlines()):
            for forward, inverse, label in ((search_heading, search_unheading, 'headroom.search_heading'),
                                             (search_dir_heading, search_dir_unheading, 'headroom.search_dir_heading')):
                candidate = forward(text)
                if inverse(candidate) == text:
                    candidates.append((candidate, label))
        if sum(line.lstrip().startswith(('INFO ', 'WARN ', 'ERROR ', 'DEBUG ', 'WARNING ')) for line in text.splitlines()) >= 3:
            candidate = collapse_runs(text)
            if expand_runs(candidate) == text:
                candidates.append((candidate, 'headroom.collapse_runs'))
        if candidates:
            candidate, label = min(candidates, key=lambda value: len(value[0].encode()))
            if len(candidate.encode()) < len(text.encode()):
                text, name, reversible = candidate, label, True
    if name is None:
        return original, None
    digest = hashlib.sha256(original.encode()).hexdigest()
    notice = ('All source lines are represented reversibly; repeated markers count occurrences and search headings apply to following rows.' if reversible
              else 'Only exact transient Docker progress lines removed; other lines retained.')
    header = f'[TTGL live tool presentation: {name}. {notice} Raw SHA256 {digest}; retrieve with read_compression_source.]\n'
    candidate = header + text
    # Do not increase context or make marginal folds that cost more to explain.
    if len(candidate.encode()) > len(original.encode()) * .8 or len(original.encode()) - len(candidate.encode()) < 256:
        return original, None
    return candidate, dict(kind=name, reversible=reversible, source_sha256=digest,
                           original_bytes=len(original.encode()), forwarded_bytes=len(candidate.encode()))


def transform_request(document, policy, retain_source=None):
    """Only descend inside completed tool-output nodes. All other nodes stay identical."""
    if policy not in POLICIES:
        raise ValueError('Unknown compression policy')
    started = time.perf_counter()
    changes = []
    if policy == 'off' or not isinstance(document, dict) or not isinstance(document.get('input'), list):
        return document, dict(policy=policy, changes=[], elapsed_seconds=time.perf_counter()-started)

    def visit(value, path, call_id):
        if isinstance(value, str):
            # Native code mode sometimes serializes nested tool JSON into a text block.
            # Parse only entire JSON values and preserve wrapper/status metadata.
            try:
                parsed = json.loads(value)
            except (ValueError, TypeError):
                parsed = None
            if isinstance(parsed, (dict, list)):
                previous = len(changes)
                updated = visit(parsed, path + ['json'], call_id)
                return json.dumps(updated, ensure_ascii=False) if len(changes) > previous else value
            updated, change = transform_text(value, policy)
            if change:
                if retain_source:
                    retain_source(change['source_sha256'], value)
                changes.append(dict(**change, path=path, call_id=call_id))
            return updated
        if isinstance(value, list):
            return [visit(item, path+[index], call_id) for index, item in enumerate(value)]
        if isinstance(value, dict):
            # Never alter result identifiers, flags, exit codes, schema or non-text values.
            return {key: visit(item, path+[key], call_id) if key in ('output', 'aggregated_output', 'text', 'content', 'result', 'content_blocks') else item
                    for key, item in value.items()}
        return value

    inputs = []
    try:
        for index, item in enumerate(document['input']):
            if isinstance(item, dict) and item.get('type') in ('custom_tool_call_output', 'function_call_output') and 'output' in item:
                # Raw retrievals must never be re-compressed, including nested JSON.
                if RAW_MARKER in json.dumps(item['output']):
                    inputs.append(item)
                else:
                    inputs.append({**item, 'output': visit(item['output'], ['input', index, 'output'], item.get('call_id'))})
            else:
                inputs.append(item)
    except Exception as exc:
        return document, dict(policy=policy, changes=[], elapsed_seconds=time.perf_counter()-started, passthrough_reason=type(exc).__name__)
    return {**document, 'input': inputs}, dict(policy=policy, changes=changes, elapsed_seconds=time.perf_counter()-started)
