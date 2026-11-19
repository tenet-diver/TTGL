"""Common native episode adapter for frozen accumulation/comparison assignments.

Learned baselines are injected as qualified released instances, never imported
from an arbitrary JSON factory or replaced by a heuristic. No implicit installs.
"""
from __future__ import annotations
import json
import difflib
import shutil
import time
from pathlib import Path
from ..experience_routing.checkpoints import manifest
from ..experience_routing.io import digest, write_new, read, file_digest, now
from .accumulation import retrieve
from .episode import run_episode


def scenario_cost(usage, rates):
    required = ('input_tokens', 'cached_input_tokens', 'output_tokens')
    if any(usage.get(k) is None for k in required):
        return None
    i, c, o = (usage[k] for k in required)
    if c > i:
        raise ValueError('Cached input exceeds total input')
    return ((i-c)*rates['input']+c*rates['cached']+o*rates['output'])/1e6


def coding_candidate_text(task, result, source, public_check):
    diffs = []
    original = Path(task['source'])
    for name in result['changed_paths']:
        before, after = original/name, Path(source)/name
        a = before.read_text(errors='replace').splitlines(True) if before.is_file() else []
        b = after.read_text(errors='replace').splitlines(True) if after.is_file() else []
        diffs.extend(difflib.unified_diff(a, b, fromfile='a/'+name, tofile='b/'+name))
    source_diff = ''.join(diffs)
    return json.dumps({'model_report': result['model_report'],
        'public_check_passed': result['public_check_passed'], 'source_diff': source_diff[:16000],
        'source_diff_clipped': len(source_diff) > 16000, 'public_check_output': public_check['output'][:8000],
        'public_check_output_clipped': len(public_check['output']) > 8000,
        'candidate_artifact': result['candidate_archive']}, sort_keys=True)


class NativeCampaignRunner:
    def __init__(self, *, root, tasks, snapshots, config, routellm=None, frugalgpt_factory=None):
        self.root, self.tasks, self.snapshots, self.config = Path(root), tasks, snapshots, config
        self.routellm, self.frugalgpt_factory = routellm, frugalgpt_factory

    def candidate_source(self, assignment, folder, index):
        scratch = self.config.get('candidate_root')
        if scratch:
            return Path(scratch) / digest(assignment) / str(index) / 'source'
        return Path(folder) / ('candidate-' + str(index)) / 'source'

    def __call__(self, assignment, folder):
        config = self.config
        task = self.tasks[assignment['task_id']]
        snapshot = self.snapshots[assignment['snapshot_id']]
        query = {**task['features'], 'task_id': task['task_id'], 'goal': task['prompt']}
        common = retrieve(snapshot, query, maximum_bytes=config['maximum_packet_bytes'])
        write_new(Path(folder)/'common-packet.json', common)
        started = time.monotonic()
        results = []
        sources = []
        episodes = []

        def solve(model, *, delegation=None, remaining=None):
            candidate_folder = Path(folder)/('candidate-'+str(len(results)))
            source = self.candidate_source(assignment, folder, len(results))
            original = Path(task['source'])
            if manifest(original)['state_hash'] != task['source_state_hash']:
                raise ValueError('Frozen public task source drift')
            shutil.copytree(original, source, ignore=shutil.ignore_patterns('.git'))
            limits = remaining or assignment['limits']
            if limits['maximum_invocations'] < 1:
                raise ValueError('Shared native episode invocation cap exhausted')
            episode = candidate_folder/'run'
            result = run_episode(root=self.root, output=episode, source=source,
                source_home=config['source_home'], model=model, image_review=config['image_review'],
                task=task, packet=common, timeout_seconds=min(limits['maximum_elapsed_seconds'], config['per_call_timeout']),
                maximum_tool_calls=config['maximum_tool_calls'], delegation=delegation,
                registration=config['registration'])
            results.append(result)
            sources.append(source)
            episodes.append(episode)
            return result

        system = assignment['system']
        if system in ('luna', 'sol'):
            final = solve('gpt-6-luna' if system == 'luna' else 'gpt-6.1-sol')
        elif system == 'routellm_native':
            if self.routellm is None:
                raise ValueError('Actual qualified released RouteLLM instance is unavailable')
            # Every family can see the same packet; the learned route can use
            # public task and common knowledge, not task outcomes.
            public = json.dumps({'goal': task['prompt'], 'knowledge': common}, sort_keys=True)
            selection = self.routellm.select(public, config['routellm_thresholds'][assignment['point']])
            write_new(Path(folder)/'router-selection.json', selection)
            final = solve(selection['model'])
        elif system == 'observatory':
            point_config = config.get('delegation_by_point', {}).get(assignment['point'])
            if point_config is None:
                if assignment['point'] != 'balanced':
                    raise ValueError('Frozen Observatory configuration required for this operating point')
                point_config = config['delegation']
            cfg = {**point_config, 'task': task, 'experiences': snapshot['experiences'],
                   'registration': config['registration'], 'now': now()}
            if config.get('candidate_root'):
                cfg['worker_scratch_root'] = str(Path(config['candidate_root'])/digest(assignment)/'workers')
            # The tool uses the same immutable snapshot. Public attribution,
            # source/time exclusions and evidence routing still precede dispatch.
            cfg['context'] = {**cfg['context'], 'watermark': config['publication_watermark']}
            final = solve('gpt-6.1-sol', delegation=cfg)
        elif system == 'frugalgpt_native':
            if self.frugalgpt_factory is None:
                raise ValueError('Actual qualified released FrugalGPT instance is unavailable')
            baseline = self.frugalgpt_factory(assignment['point'])
            def candidate(model, query, remaining):
                result = solve(model, remaining=remaining)
                if result['status'] not in ('completed', 'public_failure'):
                    return {'status': 'uncertain'}
                cost = scenario_cost(result['total_native_usage'], config['rates'][model])
                public_check = read(episodes[-1]/'public-check.json')
                return {'status': result['status'], 'candidate_text': coding_candidate_text(task, result, sources[-1], public_check),
                    'public_trace_hash': result['candidate_archive']['sha256'],
                    'checkpoint_id': result['candidate_hash'], 'scenario_cost': cost,
                    'usage': {'tokens': result['total_native_usage']['total_tokens'],
                              'elapsed_seconds': result['usage']['maximum_elapsed_seconds']}}
            baseline.run(json.dumps({'goal': task['prompt'], 'knowledge': common}, sort_keys=True), candidate, assignment['limits'])
            final = results[-1]
        else:
            raise ValueError('Unregistered comparative system')
        # Charge every candidate and worker. Final-only accounting is forbidden.
        usage = {k: sum(r['usage'][k] for r in results) if all(r['usage'][k] is not None for r in results) else None
                 for k in assignment['limits']}
        usage['maximum_elapsed_seconds'] = time.monotonic()-started
        return {'status': final['status'], 'usage': usage, 'packet_hash': digest(common),
                'candidate_artifact': final['candidate_archive'], 'candidate_hash': final['candidate_hash'],
                'native_attempts': results, 'actual_cash': None, 'grades_sealed': True}
