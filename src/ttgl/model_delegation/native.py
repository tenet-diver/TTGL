"""Autonomous native node execution through existing reviewed TTGL adapters.

This module is deliberately lazy: routing/MCP inspection and replay need no
native runtime or third-party install. Construction requires operator-owned
workspace/check catalogue, retained client, and positive campaign budget.
"""
from __future__ import annotations
import os
from pathlib import Path
from ..experience_routing.io import digest, read, write_new, file_digest


def worker_from_freeze(path, *, service_config):
    """Attach native execution only to an exact, qualified operator freeze.

    A durable campaign-start marker forbids reinitializing spent budgets on
    restart. Reconciliation/resume is intentionally not guessed by this adapter.
    """
    if file_digest(path) != service_config.get('native_freeze_sha256'):
        raise ValueError('Native freeze hash differs from host configuration')
    frozen = read(path)
    for pin in frozen['pins'].values():
        if file_digest(pin['path']) != pin['sha256']:
            raise ValueError('Frozen source/runtime/receipt drift')
    required = {'dependency_review', 'source_binding', 'actor_boundary', 'native_metering',
                'capture_roundtrip', 'benchmark_controls', 'reservation_audit'}
    readiness_pin = frozen['pins']['readiness']
    readiness = read(readiness_pin['path'])
    if readiness.get('execution_ready') is not True or any(readiness.get('gates', {}).get(k) != 'passed' for k in required):
        raise ValueError('Actual native readiness receipts are incomplete')
    cfg = frozen['worker']
    if cfg['account_hash'] != service_config['context']['account_hash']:
        raise ValueError('Worker and tool source identities differ')
    if frozen['experience_hash'] != digest(read(service_config['experiences'])) or frozen['capability_hash'] != digest(read(service_config['models'])):
        raise ValueError('Frozen experience/capability snapshot changed')
    from ..experience_routing.client import ExperienceClient
    from ..experience_routing.ledger import Budget
    context = service_config['context']
    client = ExperienceClient(context['project'], context['study'], endpoint=frozen['experience_endpoint'])
    budget = Budget(**frozen['campaign_budget'])
    worker = NativeNodeWorker(config=cfg, client=client, campaign_budget=budget)
    write_new(Path(service_config['output'])/'campaign-started.json',
              {'freeze_hash': file_digest(path), 'automatic_budget_reset': False, 'automatic_retry': False})
    return worker


class NativeNodeWorker:
    fixture_only = False

    def __init__(self, *, config, client, campaign_budget):
        if os.environ.get('OBS_ALLOW_DELEGATION_MODELS') != '1' or config.get('allow_model_execution') is not True:
            raise ValueError('An enabled finite native delegation freeze is required')
        from ..experience_routing.backend import source_binding
        binding = source_binding(config['source_home'])
        if binding['account_hash'] != config['account_hash']:
            raise ValueError('Collector subscription binding differs')
        if client is None or campaign_budget is None:
            raise ValueError('Retained local artifacts and shared campaign budget required')
        for key in ('maximum_invocations', 'maximum_tokens', 'maximum_elapsed_seconds'):
            value = config['per_attempt'][key]
            if isinstance(value, bool) or not isinstance(value, (float, int)) or value <= 0:
                raise ValueError('Positive attempt limit required: ' + key)
        self.config, self.client, self.campaign_budget = config, client, campaign_budget

    def __call__(self, request, contract, decision, evidence, folder):
        from ..experience_routing.backend import RecordedCodexBackend, source_binding
        from ..experience_routing.execution import DockerWorkspace
        from ..experience_routing.checkpoints import CheckpointStore, manifest
        from ..experience_routing.ledger import Budget, UsageLedger
        from ..experience_routing.runtime import Invocations, ParentRunner
        from ..experience_routing.policy import RoutingPolicy
        from ..experience_routing.verification import PublicVerifier
        cfg, folder = self.config, Path(folder)
        self.campaign_budget.check()
        source = Path(cfg['workspace']).resolve(strict=True)
        if source_binding(cfg['source_home'])['account_hash'] != cfg['account_hash']:
            raise ValueError('Source binding changed before worker dispatch')
        if manifest(source)['state_hash'] != contract['base_checkpoint']:
            raise ValueError('Parent checkpoint is stale')
        if not set(contract['acceptance_checks']).issubset(cfg['check_catalog']):
            raise ValueError('Unknown host-owned acceptance check')
        selected = decision['selected_model']
        if selected not in cfg['models']:
            raise ValueError('Unregistered native executor')
        actor = DockerWorkspace(image=cfg['image'], review=read(cfg['image_review']), root=folder/'actor',
                                identity=decision['decision_id'], base_commit=cfg['base_commit'])
        budget = Budget(**cfg['per_attempt'])
        ledger = UsageLedger(folder/'accounting', cfg['rates'])
        container = actor.start(source)
        try:
            backend = RecordedCodexBackend(executable=cfg['codex_executable'], executable_sha256=cfg['codex_sha256'],
                source_home=cfg['source_home'], source_account_hash=cfg['account_hash'], output=folder/'native',
                client=self.client, container=container, node_executable=cfg['node_executable'])
            calls = Invocations(folder/'invocations', backend, ledger, budget, client=self.client, campaign_budget=self.campaign_budget,
                                origin='fixture' if getattr(backend, 'fixture_only', False) else 'native')
            revision = digest([decision['decision_id'], contract])
            node = {'nodeId': digest(contract), 'planRevisionId': revision, 'parentWorkItemId': request['task_id'],
                'goal': request['goal'], 'allowedWritePaths': contract['allowed_write_paths'], 'dependsOn': [],
                'preconditions': [], 'publicVerificationCommands': [],
                'acceptanceCriteria': [{'id': k, 'description': cfg['check_catalog'][k].get('description', k), 'publicCheck': None} for k in contract['acceptance_checks']],
                'relevantPaths': contract['allowed_write_paths'], 'relevantSymbols': [], 'expectedArtifacts': contract['allowed_write_paths'],
                'estimatedDifficulty': 'routine', 'delegationSuitability': 'bounded', 'supersedesNodeIds': []}
            plan = {'planRevisionId': revision, 'taskInstanceId': request['task_id'], 'previousRevisionId': None,
                    'nodes': [node], 'continuedNodeIds': [], 'cancelledNodeIds': [],
                    'contextHash': digest(request), 'plannerInvocationId': 'parent-contract-'+digest(contract)}
            checkpoints = CheckpointStore(folder/'checkpoints', source, base_commit=cfg['base_commit'], environment_digest=cfg['image'])
            initial = checkpoints.capture(request['task_id'], node['nodeId'], node)
            self.client.retain_file(initial['archive_path'], kind='delegation-checkpoint', identity=initial['checkpointId'])
            verifier = PublicVerifier(cfg['check_catalog'], cfg.get('protected_paths', []), folder/'checks', executor=actor.public_check)
            # Worker keeps its native tool conversation during this autonomous
            # attempt. There is no per-action classifier or automatic fallback.
            policy = RoutingPolicy(small=selected, large=selected, mode='all_large')
            runtime = {'mode': 'frozen_memory', 'watermark': cfg['watermark'], 'memory_snapshot_id': cfg['snapshot_id'],
                       'policy_version': 'tool-similarity-recency-v1', 'models': cfg['models'],
                       'maximum_large_fallbacks_per_node': 0, 'maximum_parent_replans': 0}
            memory = {'experiences': [{'versionId': e['id'], 'admission': 'publicly_supported',
                'procedure': [], 'goal': e['goal'], 'outcome': e['outcome'], 'supportKind': 'execution_outcome',
                'sourceVerificationRef': e['verification_ref']} for e in evidence['experiences']]}
            memory['experiences'] += [{'versionId': g['id'], 'admission': 'publicly_supported',
                'procedure': g['procedure'], 'preconditions': g['preconditions'], 'acceptanceCriteria': g['acceptance_criteria'],
                'sourceModel': g['source_model'], 'sourceAssistance': g['source_assistance'],
                'evidenceRefs': g['evidence_refs'], 'supportKind': 'grounded_procedure'}
                for g in evidence.get('guidance', [])]
            result = ParentRunner(task={'task_id': request['task_id'], 'prompt': request['goal']}, arm='tool-delegation',
                workspace=source, checkpoints=checkpoints, verifier=verifier, invocations=calls, policy=policy,
                memory=lambda *args: memory, output=folder/'worker', config=runtime,
                client=None, execution_context=actor).run(plan)
            state = result['public_state']
            retained = []
            for path in sorted((folder/'checks').glob('*.json')) + sorted((folder/'accounting').glob('*.jsonl')):
                retained.append(self.client.retain_file(path, kind='delegation-evidence', identity=digest([decision['decision_id'], str(path.relative_to(folder))])))
            if (result.get('artifact') or {}).get('archive_path'):
                retained.append(self.client.retain_file(result['artifact']['archive_path'], kind='delegation-result', identity=result['artifact']['checkpointId']))
            return {'status': 'public_checks_passed' if state == 'completed' else 'uncertain' if state == 'uncertain' else 'needs_parent',
                    'selected_model': selected, 'public_state': state, 'worker_receipt': str(folder/'worker'),
                    'artifact': result.get('artifact'), 'usage': budget.receipt(), 'accounting': ledger.totals(),
                    'retained_evidence': retained, 'benchmark_grade': None}
        finally:
            actor.close()
