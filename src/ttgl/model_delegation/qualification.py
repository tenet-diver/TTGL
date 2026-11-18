"""Finite source-bound native transport qualification, separate from task scores."""
from __future__ import annotations
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from ..experience_routing.backend import RecordedCodexBackend, source_binding
from ..experience_routing.io import digest, file_digest, read, write_new, now
from ..experience_routing.ledger import UsageLedger
from ..personal import Request
from .retention import LocalS3Retention


def qualify_transport(root, output, *, source_home, protocol):
    root, output = Path(root).resolve(), Path(output).resolve()
    p = read(protocol)
    if (p.get('stage') != 'transport_qualification' or p.get('allow_model_execution') is not True
            or p.get('automatic_retries') != 0 or p.get('maximum_invocations') != 2
            or p.get('models') != ['gpt-6-luna', 'gpt-6.1-sol']):
        raise ValueError('Exact finite native transport registration required')
    binding = source_binding(source_home)
    executable = str(Path(shutil.which('codex')).resolve(strict=True))
    if p['codex_sha256'] != file_digest(executable):
        raise ValueError('Native executable differs from registration')
    if p['source_account_hash'] != binding['account_hash']:
        raise ValueError('Registered source subscription differs')
    for pin in p['source_pins']:
        if file_digest(root/pin['path']) != pin['sha256']:
            raise ValueError('Qualification source drift')
    client = LocalS3Retention(root, output/'retention')
    # Establish real S3/PG exact read-back BEFORE authorizing a model call.
    retained = client.retain_file(protocol, kind='qualification-registration', identity=digest(p))
    write_new(output/'started.json', {'protocol_sha256': file_digest(protocol), 'source_binding': binding,
                                    'registration_archive': retained, 'started_at': now()})
    workspace = output/'empty-workspace'
    workspace.mkdir(mode=0o700)
    backend_type = RecordedCodexBackend
    if p.get('transport_version') == 'named-subscription-provider-v1':
        from .transport import SubscriptionBackend
        backend_type = SubscriptionBackend
    backend = backend_type(executable=executable, executable_sha256=p['codex_sha256'],
        source_home=source_home, source_account_hash=binding['account_hash'], output=output/'native', client=client)
    ledger = UsageLedger(output/'accounting')
    rows = []
    for i, model in enumerate(p['models']):
        ident = 'transport-'+str(i+1)
        write_new(output/ident/'started.json', {'model': model, 'automatic_retry': False})
        schema = {'type': 'object', 'additionalProperties': False, 'required': ['marker'],
                  'properties': {'marker': {'type': 'string'}}}
        request = Request(ident, model, 'transport_qualification',
            'Return exactly this JSON object: {"marker":"observatory-transport-ok"}. Do not use tools.',
            workspace, schema, p['timeout_seconds'], read_only=True, reasoning_effort='low')
        try:
            response = backend.complete(request)
            write_new(output/ident/'response.json', asdict(response))
            row = ledger.record(request, response, 'research_audit', 'research_measurement',
                                backend.last_native_artifact_hash, response_ids=backend.last_response_ids)
            accepted = (response.status == 'completed' and not response.tool_events
                        and json.loads(response.text) == {'marker': 'observatory-transport-ok'}
                        and (row['delta'].get('total_tokens') or 0) > 0)
            outcome = {'model': model, 'passed': accepted, 'status': response.status,
                       'error_type': response.error_type, 'usage': row['delta'],
                       'elapsed_seconds': response.elapsed_seconds, 'tool_count': len(response.tool_events)}
            rows.append(outcome)
            write_new(output/ident/'completion.json', outcome)
            if not accepted:
                raise ValueError('Native transport did not qualify; preserve attempt without retry')
        except BaseException as error:
            write_new(output/'stopped.json', {'reason': type(error).__name__, 'completed': rows,
                      'automatic_retry': False, 'benchmark_trials': 0})
            raise
    report = {'stage': 'transport_qualification', 'passed': True, 'models': rows,
              'benchmark_trials': 0, 'coding_actor_qualified': False,
              'actual_cash': None, 'new_model_invocations': len(rows), 'finished_at': now()}
    write_new(output/'completion.json', report)
    return report
