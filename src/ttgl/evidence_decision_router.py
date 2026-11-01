"""Consolidated general policy, matched common guidance for Sol and Luna router."""
import asyncio
import json
import hashlib
from dataclasses import replace
from pathlib import Path
import time

from . import benchmark, personal, policy
from .actor_boundary import check_actor
from .harbor_routing_agent import DiagnosticBackend, RoutingDiagnosticCodex

COMMON = policy.PROMPTS/'controller-v9-common.txt'
ROUTING = policy.PROMPTS/'controller-v9-routing.txt'


EVIDENCE_FIELDS = {
    'verification_status': {'type':'string','enum':['supported','contradicted','incomplete']},
    'acceptance_evidence': {'type':'string'},
    'attempt_evidence': {'type':'string'},
    'material_gaps': {'type':'string'},
    'escalation_reason': {'type':'string'},
}

def evidence_schema(schema):
    return personal._schema({**schema['properties'], **EVIDENCE_FIELDS})


class EvidenceDecisionBackend(DiagnosticBackend):
    def diagnostic_identity(self):
        return {'mode': 'consolidated-v9', 'source_sha256': benchmark.digest(Path(__file__)),
                'common_sha256': benchmark.digest(COMMON),
                'routing_sha256': benchmark.digest(ROUTING),
                'transport_sha256': benchmark.digest(Path(__file__).with_name('harbor_bridge.py')),
                'completion_evidence_schema_sha256': personal._digest(EVIDENCE_FIELDS),
                'snapshot_source_sha256': benchmark.digest(Path(__file__).with_name('harbor_routing_agent.py'))}

    def describe(self):
        return {**super().describe(), 'controller_policy': self.diagnostic_identity()}

    def complete(self, request):
        if self.diagnostic_identity() != self.frozen_diagnostic:
            raise ValueError('Consolidated policy or transport changed during execution')
        capture_seconds = 0
        if request.kind == 'expert' and not (self.records/'pre-handoff.json').exists():
            began = time.monotonic()
            future = self.bridge.execution_context.copy().run(
                asyncio.run_coroutine_threadsafe, self.capture_candidate(request), self.bridge.loop)
            try:
                future.result(timeout=50)
            except BaseException:
                future.cancel()
                raise
            capture_seconds = time.monotonic()-began
            request = replace(request, timeout_seconds=max(0, request.timeout_seconds-capture_seconds))
        prompt = request.prompt
        if request.kind == 'controller' and request.thread_id is None:
            prompt += '\n\nGeneral solving and verification policy v9:\n'+COMMON.read_text()
            if 'You are the small agent. Act yourself where useful.' in request.prompt:
                prompt += '\n\nVoluntary consultation policy v9:\n'+ROUTING.read_text()
        if not request.read_only:
            prompt += ('\nUse only the worker shell MCP tool for repository work. Its repository is '
                       + self.bridge.repository+' inside the assigned environment; the host workspace is empty.')
        benchmark.write_new(self.audit_root/(personal._digest(request.request_id)+'.json'), {
            'request_id':request.request_id,'kind':request.kind,'prompt':prompt,
            'policy':self.frozen_diagnostic})
        if not request.read_only:
            self.bridge.active_request = {'request_id':request.request_id,'model':request.model,'kind':request.kind}
        try:
            # Keep the supported Codex/MCP command path, without stacking archived
            # v2/v3/v4/v6 policy text onto this separately registered treatment.
            effective_schema = evidence_schema(request.schema) if request.kind == 'controller' else request.schema
            response = personal.CodexBackend.complete(self, replace(request,prompt=prompt,schema=effective_schema))
            if request.kind == 'controller' and response.status == 'completed':
                response = self.record_decision(request,response,effective_schema)
            if capture_seconds:
                response.elapsed_seconds += capture_seconds
            return response
        finally:
            if not request.read_only:
                self.bridge.active_request = {}


    def record_decision(self, request, response, schema):
        # Format scaffolding only: preserve Luna's action and every token/timing
        # field. Never convert a gap, exit code or hidden grade into escalation.
        record={'request_id':request.request_id,'controller_policy':self.frozen_diagnostic,
                'native_output_sha256':hashlib.sha256(response.text.encode()).hexdigest(),
                'native_text':response.text}
        try:
            value=personal._response_json(response,schema)
            record['decision']=value
            projected={key:value[key] for key in request.schema['properties']}
            response=replace(response,text=json.dumps(projected,ensure_ascii=False))
        except (ValueError,TypeError,KeyError) as exc:
            record['parse_error']=type(exc).__name__
            response=replace(response,status='failed',error_type='decision_evidence_schema')
        try:
            benchmark.write_new(self.records/'decision-evidence'/(personal._digest(request.request_id)+'.json'),record)
        except OSError:
            # Do not discard already observed native usage on an audit-write failure.
            return replace(response,status='failed',error_type='decision_evidence_write')
        return response


class EvidenceDecisionCodex(RoutingDiagnosticCodex):
    @staticmethod
    def name():
        return 'ttgl-evidence-decision-v9'

    def make_backend(self, bridge, records):
        if self.policy != 'verification' or self.condition not in ('personal','large'):
            raise ValueError('Matched v9 requires voluntary router or Sol-only condition')
        return EvidenceDecisionBackend(bridge, diagnostic='verification', records=records)

    async def run(self, instruction, environment, context):
        boundary = await check_actor(environment,self.repository,self.base_head,self.private_records_root)
        benchmark.write_new(self.logs_dir/'actor-boundary.json',boundary)
        await super().run(instruction,environment,context)
        context.metadata['fresh_actor_boundary'] = boundary
