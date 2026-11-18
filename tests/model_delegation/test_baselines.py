import copy
import unittest
from ttgl.model_delegation.baselines import RouteLLMNative, FrugalGPTNative, NativeCandidateEngine


def receipt(method):
    return {'method': method, 'qualified': True, 'upstream_commit': 'a'*40,
            'implementation_sha256': 'b'*64, 'parameters_sha256': 'c'*64,
            'security_receipt_sha256': 'd'*64, 'models': ['gpt-6-luna', 'gpt-6.1-sol'],
            'training_partition': 'development', 'training_ids': ['train0', 'train1'],
            'sufficiency_passed': True, 'runtime_api_key': False, 'runtime_remote_encoder': False}


class BaselineTests(unittest.TestCase):
    def test_routellm_invokes_actual_router_once_without_outcomes(self):
        class Router:
            calls = 0
            def calculate_strong_win_rate(self, prompt): return .8
            def route(self, prompt, threshold, pair):
                self.calls += 1
                return pair.strong if self.calculate_strong_win_rate(prompt) >= threshold else pair.weak
        router = Router()
        a = RouteLLMNative(router, receipt('routellm_native'), evaluation_ids=['test'])
        self.assertEqual(a.select('public input', .7)['model'], 'gpt-6.1-sol')
        self.assertEqual(router.calls, 1)
        self.assertEqual(a.select('public input', .9)['model'], 'gpt-6-luna')

    def test_unqualified_leaky_unpinned_and_remote_paths_rejected(self):
        for key, value in [('qualified', False), ('upstream_commit', ''), ('training_ids', ['test']),
                           ('models', ['other', 'sol']), ('sufficiency_passed', False), ('runtime_api_key', True),
                           ('runtime_remote_encoder', True)]:
            r = receipt('routellm_native'); r[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                RouteLLMNative(None, r, evaluation_ids=['test'])

    def candidate(self, model, prompt, remaining):
        return {'status': 'completed', 'candidate_text': model+' candidate', 'checkpoint_id': model+'-checkpoint',
                'public_trace_hash': 'trace', 'scenario_cost': .1,
                'usage': {'tokens': 100, 'elapsed_seconds': 2}}

    def test_frugal_preserves_learned_scorer_cascade_and_charges_all_candidates(self):
        class LearnedCascade:
            # Synthetic interface fixture, not claimed as released inference.
            MyScores = {'luna': 'pinned quality model'}
            LLMChain = 'pinned trained thresholds'
            def get_completion(self, query, genparams):
                first = self.MyLLMEngine.get_completion(query=query, service_name='gpt-6-luna', genparams=genparams)
                self.cost = self.MyLLMEngine.get_cost()
                second = self.MyLLMEngine.get_completion(query=query, service_name='gpt-6.1-sol', genparams=genparams)
                self.cost += self.MyLLMEngine.get_cost()
                return second
        r = receipt('frugalgpt_native')
        adapter = FrugalGPTNative(LearnedCascade(), r, evaluation_ids=['test'])
        limits = {'maximum_invocations': 2, 'maximum_tokens': 300, 'maximum_elapsed_seconds': 10}
        calls = []
        def execute(model, prompt, remaining):
            calls.append(copy.deepcopy(remaining))
            return self.candidate(model, prompt, remaining)
        result = adapter.run('public prompt', execute, limits)
        self.assertEqual(result['scenario_cost'], .2)
        self.assertEqual(result['tokens'], 200)
        self.assertEqual(calls[1]['maximum_tokens'], 200)
        with self.assertRaises(ValueError): adapter.run('public prompt', execute, limits)

    def test_public_check_fallback_is_not_accepted_as_frugalgpt(self):
        with self.assertRaises(ValueError): FrugalGPTNative(object(), receipt('frugalgpt_native'), evaluation_ids=[])

    def test_uncertainty_and_hidden_feedback_stop_without_fallback(self):
        limits = {'maximum_invocations': 2, 'maximum_tokens': 300, 'maximum_elapsed_seconds': 10}
        for changes in [{'status': 'uncertain'}, {'resolved': True}, {'usage': {'tokens': 301, 'elapsed_seconds': 1}}]:
            with self.subTest(changes=changes):
                engine = NativeCandidateEngine(lambda *args: {**self.candidate(*args), **changes}, limits)
                with self.assertRaises(ValueError): engine.get_completion(query='q', service_name='gpt-6-luna', genparams=None)
                self.assertEqual(len(engine.results), 1)
