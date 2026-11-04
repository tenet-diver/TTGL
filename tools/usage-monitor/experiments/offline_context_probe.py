#!/usr/bin/env python3
"""Dependency-free adapter mechanism diagnostics. No model, network or Headroom import."""
import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from datetime import datetime, timezone
import context_pilot as pilot


def probe():
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
    with tempfile.TemporaryDirectory(prefix='ttgl-context-probe-') as tmp:
        data = pilot.fixtures(pathlib.Path(tmp))
        outputs = [{'type': 'function_call_output', 'call_id': f'call-{i}',
                    'output': json.dumps(data['inventory'][i])} for i in range(3)]
        body = {'input': [{'type': 'reasoning', 'id': 'opaque-reasoning',
                           'encrypted_content': 'synthetic-opaque-canary'}, *outputs],
                'previous_response_id': 'synthetic-response'}
        saved = copy.deepcopy(body)
        identity, changes = pilot.transform_body(body, 'baseline', None)
        check('baseline_identity', identity == body and not changes)
        masked, changes = pilot.transform_body(body, 'older_masking', None)
        check('full_history_masks_only_older',
              [c['observation_ref'] for c in changes] == ['inventory/0', 'inventory/1']
              and masked['input'][-1] == body['input'][-1])
        check('preserves_native_ids_and_reasoning',
              masked['input'][0] == body['input'][0]
              and [x.get('call_id') for x in masked['input']] ==
                  [x.get('call_id') for x in body['input']]
              and masked['previous_response_id'] == body['previous_response_id'])
        check('input_not_mutated', saved == body)
        delta = {'input': [outputs[-1]], 'previous_response_id': 'synthetic-response'}
        unchanged, changes = pilot.transform_body(delta, 'older_masking', None)
        check('delta_only_cannot_replace_absent_history', unchanged == delta and not changes)
        marker = ('TTGL_OBSERVATION_BEGIN inventory/0\n' +
                  json.dumps(data['inventory'][0]) + '\nTTGL_OBSERVATION_END inventory/0')
        check('marked_text_exposure_detected', pilot.ref_of(marker) == ['inventory/0'])
        nested = [{'type': 'text', 'text': marker}]
        check('nested_text_exposure_detected', pilot.ref_of(nested) == ['inventory/0'])
        class IdentityCompressor:
            def transform(self, text):
                # Adapter spy only. Byte lengths are not tokenizer measurements.
                return {'text': text, 'tokens_before': None, 'tokens_after': None,
                        'elapsed_ms': 0}, True
        transformed, changes = pilot.transform_body(body, 'headroom_insertion', IdentityCompressor())
        check('compressor_adapter_invoked_for_all_observations',
              len(changes) == 3 and all(c['kind'] == 'headroom' for c in changes))
        check('identity_compressor_preserves_payloads', all(
            json.loads(transformed['input'][i+1]['output']) == data['inventory'][i]
            for i in range(3)))
    return {'schema_version': 1, 'checked_at': datetime.now(timezone.utc).isoformat(),
            'kind': 'offline synthetic adapter diagnostics', 'checks': checks,
            'passed': all(c['passed'] for c in checks), 'model_calls': 0,
            'headroom_executed': False, 'provider_usage': None,
            'live_intervention_validated': False,
            'limitation': 'Constructed envelopes only; delta behavior is not an observation of the live Codex transport.',
            'adapter_sha256': hashlib.sha256(pathlib.Path(pilot.__file__).read_bytes()).hexdigest()}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = probe()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(result['checks']),
                      'model_calls': 0, 'headroom_executed': False}))
    raise SystemExit(0 if result['passed'] else 1)
