"""Reviewed local-feature native adaptations of released routing cores.

RouteLLM: original Router/SWRankingRouter and weighted Elo/tier functions;
native paired tables replace Arena/HF loading, local hashing replaces embeddings.
FrugalGPT: original scorer_text/get_completion and chain iteration methods;
a local learned linear quality scorer replaces the released transformer scorer.
These are explicitly adapted baselines, not published pretrained checkpoints.
No full upstream package, API client, Torch or remote encoder is imported.
"""
from __future__ import annotations
import ast
import math
import json
import types
import abc
from pathlib import Path
from ..experience_routing.io import file_digest, digest


def _selected(path, expected, names, namespace, *, class_methods=None):
    if file_digest(path) != expected:
        raise ValueError('Released component source differs from its reviewed pin')
    tree = ast.parse(Path(path).read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    if class_methods:
        nodes = [m for n in tree.body if isinstance(n, ast.ClassDef) and n.name in class_methods
                 for m in n.body if isinstance(m, ast.FunctionDef) and m.name in class_methods[n.name]]
    if not nodes:
        raise ValueError('Missing released component')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def load_cores(pins):
    # Imported only in the separately reviewed, private native classifier process.
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    context = {'np': np, 'pd': pd, 'math': math, 'abc': abc, 'LogisticRegression': LogisticRegression}
    utils = _selected(pins['routellm_utils']['path'], pins['routellm_utils']['sha256'],
                      {'compute_tiers', 'compute_elo_mle_with_tie'}, context)
    _selected(pins['routellm_routers']['path'], pins['routellm_routers']['sha256'],
              {'Router', 'SWRankingRouter'}, utils)
    cascade = _selected(pins['frugalgpt_cascade']['path'], pins['frugalgpt_cascade']['sha256'], {'scorer_text'}, {})
    _selected(pins['frugalgpt_cascade']['path'], pins['frugalgpt_cascade']['sha256'], set(), cascade,
              class_methods={'LLMCascade': {'get_completion'}})
    chain = _selected(pins['frugalgpt_chain']['path'], pins['frugalgpt_chain']['sha256'], set(), {},
                      class_methods={'LLMChain': {'reset', 'nextAPIandScore'}})
    return utils, cascade, chain


class LocalEmbeddings:
    def __init__(self, encoder):
        self.encoder = encoder
        self.embeddings = self

    def create(self, *, input, model):
        if model != 'local-char-hashing-v1' or len(input) != 1:
            raise ValueError('Only the pinned local feature path is enabled')
        return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=self.encoder.transform(input).toarray()[0])])


def hashing_encoder():
    from sklearn.feature_extraction.text import HashingVectorizer
    return HashingVectorizer(analyzer='char', ngram_range=(3, 5), n_features=2048,
                             alternate_sign=False, norm='l2', lowercase=True)


def make_routellm(cores, pairs):
    """Initialize the released similarity-weighted selector on native pairs."""
    import pandas as pd
    api, _, _ = cores
    encoder = hashing_encoder()
    rows = []
    prompts = []
    for pair in pairs:
        if type(pair.get('luna_resolved')) is not bool or type(pair.get('sol_resolved')) is not bool:
            raise ValueError('Valid disjoint native development labels required')
        a, b = pair['sol_resolved'], pair['luna_resolved']
        rows.append({'model_a': 'gpt-6.1-sol', 'model_b': 'gpt-6-luna',
                     'winner': 'model_a' if a and not b else 'model_b' if b and not a else 'tie' if a else 'tie (bothbad)'})
        prompts.append(pair['public_input'])
    if len(rows) < 2 or len(set(p['task_id'] for p in pairs)) != len(rows):
        raise ValueError('Distinct paired native development tasks required')
    frame = pd.DataFrame(rows)
    ratings = api['compute_elo_mle_with_tie'](frame)
    model2tier = api['compute_tiers'](ratings, num_tiers=2)
    # No HF/Arena constructor executes. Its exact tabular state is initialized
    # from same-harness Luna/Sol observations instead of unrelated Arena models.
    router = object.__new__(api['SWRankingRouter'])
    router.strong_model, router.weak_model = 'gpt-6.1-sol', 'gpt-6-luna'
    router.model2tier = model2tier
    router.arena_df = frame.copy()
    for column in ('model_a', 'model_b'):
        router.arena_df[column] = router.arena_df[column].apply(lambda x: model2tier[x])
    router.arena_conv_embedding = encoder.transform(prompts).toarray()
    router.embedding_model = 'local-char-hashing-v1'
    api['OPENAI_CLIENT'] = LocalEmbeddings(encoder)
    return router


class LinearQuality:
    def __init__(self, model, encoder):
        self.model, self.encoder = model, encoder

    def get_score(self, text):
        probabilities = self.model.predict_proba(self.encoder.transform([text]))[0]
        return float(probabilities[list(self.model.classes_).index(1)])


class SingleClassQuality:
    """Beta(1,1) posterior mean; no fabricated opposite-class examples.

    This has no discriminative feature learning. Report that explicitly rather
    than interpreting an observed all-pass/all-fail sample as certainty.
    """
    def __init__(self, labels):
        self.value = (sum(labels)+1)/(len(labels)+2)

    def get_score(self, text):
        return self.value


def train_quality(cores, records):
    from sklearn.linear_model import LogisticRegression
    _, cascade, _ = cores
    encoder = hashing_encoder()
    scorers, statistics = {}, {}
    for model in ('gpt-6-luna', 'gpt-6.1-sol'):
        rows = [r for r in records if r['model'] == model]
        labels = [int(r['resolved']) for r in rows if type(r.get('resolved')) is bool]
        if len(labels) != len(rows) or not labels:
            raise ValueError('Known observed native labels required; do not fabricate training examples')
        if len(set(labels)) == 1:
            scorers[model] = SingleClassQuality(labels)
            statistics[model] = {'tasks':len(rows),'successes':sum(labels),'training_only':True,
                                'scorer_kind':'beta_1_1_single_class_prior','discriminative_learning':False}
            continue
        inputs = [cascade['scorer_text'](r['public_input']+' '+r['candidate_text']) for r in rows]
        classifier = LogisticRegression(C=1.0, max_iter=500, random_state=17012026)
        classifier.fit(encoder.transform(inputs), labels)
        scorers[model] = LinearQuality(classifier, encoder)
        statistics[model] = {'tasks': len(rows), 'successes': sum(labels), 'training_only': True,
                             'scorer_kind':'local_logistic','discriminative_learning':True}
    return scorers, statistics


def make_frugalgpt(cores, scorers, strategy):
    _, methods, chain_methods = cores
    if not strategy or any(model not in scorers for model in strategy['models']):
        raise ValueError('A fitted coding scorer and development-selected strategy are required')
    Chain = type('ReleasedChainIteration', (), {k: chain_methods[k] for k in ('reset', 'nextAPIandScore')})
    chain = Chain(); chain.model_ids = strategy['models']; chain.thres = [1-t for t in strategy['quality_thresholds']]
    Cascade = type('ReleasedNativeCodingCascade', (), {'get_completion': methods['get_completion']})
    cascade = Cascade(); cascade.LLMChain = chain; cascade.MyScores = scorers
    cascade.MyLLMEngine = None; cascade.prefix = ''; cascade.score_noise_injection = False
    return cascade


def select_cascades(records, scored, *, budgets):
    """Exact exhaustive two-model cascade search on development, never test.

    This replaces the released general multi-model optimizer with an explicit
    two-model finite grid; deployment still executes its original score loop.
    Report this optimizer/scorer adaptation in every comparison.
    """
    import itertools
    by_task = {}
    for r in records:
        by_task.setdefault(r['task_id'], {})[r['model']] = r
    models = ('gpt-6-luna', 'gpt-6.1-sol')
    if not by_task or any(set(p) != set(models) for p in by_task.values()):
        raise ValueError('Complete matched development candidates required')
    candidates = []
    for order in [(m,) for m in models]+list(itertools.permutations(models)):
        for threshold in [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1]:
            cost, success = 0.0, 0
            for task, pair in by_task.items():
                selected = None
                for model in order:
                    selected = pair[model]
                    if selected.get('scenario_cost') is None:
                        raise ValueError('Development cost unknown; do not assume zero')
                    cost += selected['scenario_cost']
                    if scored[task][model] > threshold:
                        break
                success += selected['resolved']
            candidates.append({'models': list(order), 'quality_thresholds': [threshold]*len(order),
                               'mean_scenario_cost': cost/len(by_task), 'resolved': success, 'tasks': len(by_task)})
    result = {}
    for name, budget in budgets.items():
        eligible = [c for c in candidates if c['mean_scenario_cost'] <= budget]
        result[name] = min(eligible, key=lambda c: (-c['resolved'], c['mean_scenario_cost'], len(c['models']), c['quality_thresholds'][0])) if eligible else None
    return {'points': result, 'candidate_grid': candidates, 'heldout_labels_used': False}
