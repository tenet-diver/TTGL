"""Native transport adapters for qualified released router instances.

The upstream learned router/scorer must be supplied, not silently replaced by a
hand-written confidence heuristic. Importing the upstream provider servers is
unnecessary. Qualification and training receipts are separate from execution.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from .routing import number
from ..experience_routing.io import digest


@dataclass(frozen=True)
class Pair:
    weak: str = 'gpt-6-luna'
    strong: str = 'gpt-6.1-sol'


def qualify_baseline(receipt, method, *, evaluation_ids):
    if receipt.get('method') != method or receipt.get('qualified') is not True:
        raise ValueError('Actual released baseline qualification required')
    for key in ('upstream_commit', 'implementation_sha256', 'parameters_sha256', 'security_receipt_sha256'):
        v = receipt.get(key)
        if not isinstance(v, str) or len(v) not in (40, 64) or any(c not in '0123456789abcdef' for c in v):
            raise ValueError('Missing exact baseline pin: ' + key)
    if receipt.get('models') != ['gpt-6-luna', 'gpt-6.1-sol']:
        raise ValueError('Pair-specific Luna/Sol calibration required')
    if (receipt.get('training_partition') != 'development' or receipt.get('sufficiency_passed') is not True
            or not receipt.get('training_ids') or set(receipt['training_ids']) & set(evaluation_ids)):
        raise ValueError('Disjoint sufficient development calibration required')
    if receipt.get('runtime_api_key') or receipt.get('runtime_remote_encoder'):
        raise ValueError('API-key/default remote embedding paths are disabled')
    return digest(receipt)


class RouteLLMNative:
    """The real released object's route/score selects a native whole-task actor."""
    def __init__(self, router, receipt, *, evaluation_ids):
        self.pin = qualify_baseline(receipt, 'routellm_native', evaluation_ids=evaluation_ids)
        if not callable(getattr(router, 'calculate_strong_win_rate', None)) or not callable(getattr(router, 'route', None)):
            raise ValueError('Released RouteLLM router interface required')
        self.router, self.pair = router, Pair()

    def select(self, public_prompt, threshold):
        number(threshold, 'threshold')
        if threshold > 1:
            raise ValueError('Threshold exceeds one')
        # Call the released route exactly once. Do not double-score stochastic
        # routers or expose outcomes to the routing object.
        model = self.router.route(public_prompt, threshold, self.pair)
        if model not in (self.pair.weak, self.pair.strong):
            raise ValueError('Unregistered RouteLLM executor')
        return {'model': model, 'baseline_pin': self.pin, 'threshold': threshold,
                'prompt_hash': digest(public_prompt), 'level': 'whole_task'}


class NativeCandidateEngine:
    """FrugalGPT's provider engine is replaced with the shared native harness."""
    def __init__(self, execute, limits):
        self.execute, self.limits = execute, limits
        self.results, self.cost, self.elapsed = [], 0.0, 0.0
        self.tokens = 0
        self.uncertain = False

    def get_completion(self, *, query, service_name, genparams):
        if self.uncertain:
            raise ValueError('Prior candidate uncertain; no retry or fallback')
        if service_name not in ('gpt-6-luna', 'gpt-6.1-sol'):
            raise ValueError('Unregistered FrugalGPT native executor')
        if len(self.results) >= self.limits['maximum_invocations']:
            raise ValueError('Shared native cascade invocation budget')
        remaining = {**self.limits, 'maximum_invocations': self.limits['maximum_invocations']-len(self.results),
                     'maximum_tokens': self.limits['maximum_tokens']-self.tokens,
                     'maximum_elapsed_seconds': self.limits['maximum_elapsed_seconds']-self.elapsed}
        if any(v <= 0 for v in remaining.values()):
            raise ValueError('Shared cascade budget exhausted')
        self.uncertain = True
        result = self.execute(service_name, query, remaining)
        # Retain failures/unknown results before validation. Never fallback on an
        # uncertain attempt, silently discard it or reset the shared budget.
        self.results.append(result)
        if result.get('status') not in ('completed', 'public_failure'):
            raise ValueError('Uncertain native candidate; stop cascade')
        for field in ('candidate_text', 'public_trace_hash', 'checkpoint_id'):
            if not isinstance(result.get(field), str) or not result[field]:
                raise ValueError('Retained public coding candidate required: '+field)
        if any(k in result for k in ('grade', 'resolved', 'hidden_feedback')):
            raise ValueError('Hidden outcome supplied to runtime scorer')
        usage = result['usage']
        tokens = number(usage['tokens'], 'native tokens', 1)
        elapsed = number(usage['elapsed_seconds'], 'native elapsed')
        cost = number(result['scenario_cost'], 'scenario cost')
        self.tokens += tokens
        self.elapsed += elapsed
        self.cost = cost
        if self.tokens > self.limits['maximum_tokens'] or self.elapsed > self.limits['maximum_elapsed_seconds']:
            raise ValueError('Cascade exceeds shared total cap')
        self.uncertain = False
        return result['candidate_text']

    def get_cost(self):
        return self.cost


class FrugalGPTNative:
    """Preserve the released learned-score/cost-aware cascade's execution loop.

    Its pinned MyScores and LLMChain must already be trained on disjoint native
    coding episodes. Public-check fallback alone cannot instantiate this adapter.
    """
    def __init__(self, cascade, receipt, *, evaluation_ids):
        self.pin = qualify_baseline(receipt, 'frugalgpt_native', evaluation_ids=evaluation_ids)
        if (not callable(getattr(cascade, 'get_completion', None)) or not getattr(cascade, 'MyScores', None)
                or not getattr(cascade, 'LLMChain', None)):
            raise ValueError('Released learned FrugalGPT cascade required')
        self.cascade, self.used = cascade, False

    def run(self, public_prompt, execute, limits):
        if self.used:
            raise ValueError('Fresh one-episode cascade adapter required; no uncertain retry')
        for k in ('maximum_invocations', 'maximum_tokens', 'maximum_elapsed_seconds'):
            number(limits[k], k, 1)
        self.used = True
        engine = NativeCandidateEngine(execute, limits)
        self.cascade.MyLLMEngine = engine
        self.cascade.score_noise_injection = False
        # Upstream obtains candidate quality from MyScores.get_score and follows
        # its trained LLMChain thresholds. No official grade reaches that loop.
        answer = self.cascade.get_completion(public_prompt, genparams=None)
        if not engine.results or answer != engine.results[-1]['candidate_text']:
            raise ValueError('Released cascade returned an unretained native candidate')
        return {'selected_candidate': engine.results[-1], 'candidates': engine.results,
                'baseline_pin': self.pin, 'scenario_cost': sum(r['scenario_cost'] for r in engine.results),
                'actual_cash': None, 'tokens': engine.tokens, 'elapsed_seconds': engine.elapsed}
