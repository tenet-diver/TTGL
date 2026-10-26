#!/usr/bin/env python3
"""Reproduce a frozen, exploratory replay of public SWE-bench Verified outcomes.

No model APIs are called and no patches/tests are fetched. Prices are source
estimates, not invoices. Router features exclude every trajectory and gold file.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import time
import urllib.request

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import KFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'experiments/swe-replay-001/protocol.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def load_protocol(path=PROTOCOL):
    freeze = json.loads((path.parent / 'freeze.json').read_text())
    if digest(path.read_bytes()) != freeze['protocol_sha256']:
        raise ValueError('Frozen protocol hash mismatch')
    return json.loads(path.read_text())


def fetch(cache, protocol):
    """Cache public numerical records and task problem statements only."""
    cache.mkdir(parents=True, exist_ok=True)
    sources = []
    def get(relative, url):
        path = cache / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(url, timeout=45) as r:
                        body = r.read()
                    path.write_bytes(body)
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(attempt + 1)
        body = path.read_bytes()
        sources.append({'path': str(relative), 'url': url, 'sha256': digest(body), 'bytes': len(body)})
        return body
    base = f"https://raw.githubusercontent.com/{protocol['source_repository']}/{protocol['source_commit']}"
    taskbase = f"https://raw.githubusercontent.com/{protocol['task_repository']}/{protocol['task_commit']}"
    get(Path('source-readme.md'), base + '/README.md')
    get(Path('tasks-readme.md'), taskbase + '/README.md')
    records = {}
    for model, submission in protocol['models'].items():
        records[model] = json.loads(get(Path('models') / model / 'per_instance_details.json',
            f'{base}/evaluation/verified/{submission}/per_instance_details.json'))
        get(Path('models') / model / 'metadata.yaml',
            f'{base}/evaluation/verified/{submission}/metadata.yaml')
    ids = validate_records(records)
    def problem(task):
        get(Path('problems') / f'{task}.md', f'{taskbase}/tasks/{task}/problem_statement.md')
    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(problem, ids))
    manifest = {'fetched_at_utc': datetime.now(timezone.utc).isoformat(),
                'source_commit': protocol['source_commit'], 'task_commit': protocol['task_commit'],
                'license_note': 'No explicit top-level license found in the pinned experiments or task-distribution repositories. Raw texts remain ignored local cache; artifacts redistribute derived numerical facts, identifiers and hashes. Review upstream terms before redistributing raw submissions.',
                'sources': sorted(sources, key=lambda x: x['path'])}
    dump(cache / 'sources.json', manifest)
    return manifest


def validate_records(records):
    if not records:
        raise ValueError('No models')
    ids = sorted(next(iter(records.values())))
    if len(ids) != 500:
        raise ValueError(f'Expected all 500 tasks, received {len(ids)}')
    for name, rows in records.items():
        if sorted(rows) != ids:
            raise ValueError(f'Unequal task coverage: {name}')
        for task, row in rows.items():
            if type(row.get('resolved')) is not bool:
                raise ValueError(f'Missing/invalid grade: {name}/{task}')
            cost = row.get('cost')
            if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
                raise ValueError(f'Missing/invalid cost: {name}/{task}')
            calls = row.get('api_calls')
            if type(calls) is not int or calls < 0:
                raise ValueError(f'Missing/invalid API calls: {name}/{task}')
    return ids


def fit_fold(texts, repos, train, test, quality, costs):
    """Fit only train labels/costs; receive no held-out response variables."""
    vector = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=5000, sublinear_tf=True)
    length = StandardScaler()
    repository = OneHotEncoder(handle_unknown='ignore')
    train_text = [texts[i] for i in train]
    test_text = [texts[i] for i in test]
    x_train = sparse.hstack([
        vector.fit_transform(train_text),
        length.fit_transform(np.log1p([len(x) for x in train_text]).reshape(-1, 1)),
        repository.fit_transform(np.asarray(repos)[train].reshape(-1, 1))], format='csr')
    x_test = sparse.hstack([
        vector.transform(test_text),
        length.transform(np.log1p([len(x) for x in test_text]).reshape(-1, 1)),
        repository.transform(np.asarray(repos)[test].reshape(-1, 1))], format='csr')
    p = np.zeros((len(test), quality.shape[1]))
    c = np.zeros_like(p)
    for j in range(quality.shape[1]):
        y = quality[:, j]
        if len(np.unique(y)) == 1:
            p[:, j] = y[0]
        else:
            model = LogisticRegression(C=1, solver='liblinear', max_iter=2000, random_state=1729)
            model.fit(x_train, y)
            p[:, j] = model.predict_proba(x_test)[:, 1]
        reg = Ridge(alpha=1, solver='lsqr')
        reg.fit(x_train, np.log1p(costs[:, j]))
        c[:, j] = np.maximum(np.expm1(reg.predict(x_test)), 0.000001)
    return p, c


def rank_allocate(scores, fraction, ids, folds):
    """Rank within each held-out fold: own labels cannot affect other ranks."""
    selected = np.zeros(len(ids), dtype=int)
    for fold in sorted(set(folds)):
        subset = np.flatnonzero(folds == fold)
        order = np.lexsort((np.asarray(ids)[subset], -scores[subset]))
        count = int(np.floor(len(subset) * fraction + 1e-10))
        selected[subset[order[:count]]] = 1
    return selected


def bootstrap_indices(repos, repeats, cluster):
    rng = np.random.default_rng(1729)
    n = len(repos)
    if not cluster:
        return [rng.integers(0, n, n) for _ in range(repeats)]
    unique = sorted(set(repos))
    members = {r: np.flatnonzero(np.asarray(repos) == r) for r in unique}
    return [np.concatenate([members[r] for r in rng.choice(unique, len(unique), replace=True)])
            for _ in range(repeats)]


def interval_summary(q, c, baseq, basec, samples):
    delta = np.asarray([np.mean(q[s] - baseq[s]) for s in samples])
    ratio = np.asarray([np.mean(c[s]) / np.mean(basec[s]) for s in samples])
    quality = np.asarray([np.mean(q[s]) for s in samples])
    return {'resolution_ci95': np.quantile(quality, [0.025, 0.975]).tolist(),
            'paired_resolution_difference_ci95': np.quantile(delta, [0.025, 0.975]).tolist(),
            'paired_resolution_difference_lower95': float(np.quantile(delta, 0.05)),
            'paired_cost_ratio_ci95': np.quantile(ratio, [0.025, 0.975]).tolist(),
            'paired_cost_ratio_upper95': float(np.quantile(ratio, 0.95)),
            'quality_noninferiority_3pp_supported': bool(np.quantile(delta, 0.05) > -0.03),
            'at_least_25pct_inference_saving_supported': bool(np.quantile(ratio, 0.95) < 0.75),
            'joint_exploratory_target_supported': bool(np.quantile(delta, 0.05) > -0.03 and np.quantile(ratio, 0.95) < 0.75)}


def analyze(cache, output, protocol):
    if output.exists():
        raise FileExistsError('Use a fresh output directory; preserve previous analyses')
    sources = json.loads((cache / 'sources.json').read_text())
    for source in sources['sources']:
        if digest((cache / source['path']).read_bytes()) != source['sha256']:
            raise ValueError(f"Cached source hash mismatch: {source['path']}")
    names = list(protocol['models'])
    records = {name: json.loads((cache / 'models' / name / 'per_instance_details.json').read_text()) for name in names}
    ids = validate_records(records)
    texts = [(cache / 'problems' / f'{i}.md').read_text() for i in ids]
    if any(not text.strip() for text in texts):
        raise ValueError('Empty problem statement')
    repos = [i.rsplit('-', 1)[0] for i in ids]
    quality = np.asarray([[records[m][i]['resolved'] for m in names] for i in ids], dtype=float)
    costs = np.asarray([[records[m][i]['cost'] for m in names] for i in ids])
    calls = np.asarray([[records[m][i]['api_calls'] for m in names] for i in ids])
    metadata = {}
    for j, m in enumerate(names):
        raw = (cache / 'models' / m / 'metadata.yaml').read_text()
        accuracy = re.search(r'^  resolved: ([\d.]+)$', raw, re.M)
        sourcecost = re.search(r'^  cost: ([\d.eE+-]+)$', raw, re.M)
        if accuracy and abs(float(accuracy.group(1)) - 100 * quality[:, j].mean()) > 1e-7:
            raise ValueError(f'Source accuracy does not reconcile: {m}')
        if sourcecost and not math.isclose(float(sourcecost.group(1)), float(costs[:, j].sum()), rel_tol=1e-9, abs_tol=1e-8):
            raise ValueError(f'Source cost does not reconcile: {m}')
        if 'mini-swe-agent_version: 2.0.0' not in raw:
            raise ValueError(f'Harness version changed: {m}')
        metadata[m] = {'published_open_model_tag': bool(re.search(r'^  os_model: true$', raw, re.M)),
                       'published_model_id': re.search(r'^  model:\n  - ([^\n]+)', raw, re.M).group(1),
                       'metadata_total_cost_usd': float(sourcecost.group(1)) if sourcecost else None,
                       'metadata_resolution_percent': float(accuracy.group(1)) if accuracy else None,
                       'cost_reconciled_to_metadata': bool(sourcecost),
                       'zero_cost_tasks': int(np.sum(costs[:, j] == 0)),
                       'mean_api_calls': float(calls[:, j].mean())}
    p = np.zeros_like(quality)
    predicted_cost = np.zeros_like(costs)
    folds = np.zeros(len(ids), dtype=int)
    split_records = []
    started = time.perf_counter()
    for fold, (train, test) in enumerate(KFold(n_splits=5, shuffle=True, random_state=1729).split(ids)):
        folds[test] = fold
        p[test], predicted_cost[test] = fit_fold(texts, repos, train, test, quality[train], costs[train])
        split_records.append({'fold': fold, 'train': [ids[i] for i in train], 'test': [ids[i] for i in test]})
    fit_seconds = time.perf_counter() - started
    # Every choice below uses only held-out predictions/pre-task features, except
    # the explicitly labelled oracle. No grid selection is performed.
    si, li = [names.index(m) for m in protocol['primary_pair']]
    scores = {'benefit_router': p[:, li] - p[:, si],
              'cost_benefit_router': (p[:, li] - p[:, si]) / np.maximum(predicted_cost[:, li] - predicted_cost[:, si], .001),
              'length_rule': np.asarray([len(t) for t in texts]),
              'seeded_random': np.random.default_rng(1729).random(len(ids))}
    selections = {}
    policy_values = {}
    for j, name in enumerate(names):
        selections[f'always_{name}'] = np.full(len(ids), j, dtype=int)
    for fraction in protocol['large_allocation_grid']:
        for name, score in scores.items():
            route = rank_allocate(score, fraction, ids, folds)
            selections[f'{name}_large_{fraction:g}'] = np.where(route, li, si)
        policy_values[f'random_expected_large_{fraction:g}'] = ((1-fraction)*quality[:, si] + fraction*quality[:, li],
                    (1-fraction)*costs[:, si] + fraction*costs[:, li], fraction)
    for weight in protocol['portfolio_lambda_grid']:
        selections[f'portfolio_lambda_{weight:g}'] = np.argmax(p - weight * predicted_cost, axis=1)
    open_indices = [j for j, name in enumerate(names) if metadata[name]['published_open_model_tag']]
    for weight in protocol['portfolio_lambda_grid']:
        choice = np.argmax(p[:, open_indices] - weight * predicted_cost[:, open_indices], axis=1)
        selections[f'open_weight_portfolio_lambda_{weight:g}'] = np.asarray(open_indices)[choice]
    for prefix, allowed in [('pair', [si, li]), ('portfolio', list(range(len(names))))]:
        oracle = []
        for i in range(len(ids)):
            successful = [j for j in allowed if quality[i, j]]
            oracle.append(min(successful or allowed, key=lambda j: (costs[i, j], j)))
        selections[f'NONDEPLOYABLE_{prefix}_outcome_cost_oracle'] = np.asarray(oracle)
    indices = np.arange(len(ids))
    for name, selected in selections.items():
        policy_values[name] = (quality[indices, selected], costs[indices, selected], float(np.mean(selected == li)))
    task_boot = bootstrap_indices(repos, 2000, False)
    cluster_boot = bootstrap_indices(repos, 2000, True)
    summaries = []
    for name, (q, c, fraction) in policy_values.items():
        row = {'policy': name, 'tasks': len(ids), 'resolved': float(q.sum()), 'resolution_rate': float(q.mean()),
               'estimated_inference_total_usd': float(c.sum()), 'estimated_inference_usd_per_task': float(c.mean()),
               'estimated_inference_usd_per_resolved_task': float(c.sum()/q.sum()) if q.sum() else None,
               'inference_saving_vs_large_fraction': float(1-c.sum()/costs[:, li].sum()),
               'resolution_difference_vs_large': float(q.mean()-quality[:, li].mean()),
               'large_model_fraction': fraction, 'nondeployable_oracle': name.startswith('NONDEPLOYABLE'),
               'break_even_added_overhead_usd_per_task': float(costs[:, li].mean()-c.mean()),
               'remaining_overhead_for_25pct_saving_usd_per_task': float(.75*costs[:, li].mean()-c.mean()),
               'task_bootstrap': interval_summary(q,c,quality[:,li],costs[:,li],task_boot),
               'repository_cluster_bootstrap': interval_summary(q,c,quality[:,li],costs[:,li],cluster_boot),
               'overhead_sensitivity': [{'extra_usd_per_task': h, 'inference_plus_assumed_overhead_usd_per_task': float(c.mean()+h),
                    'saving_fraction': float(1-(c.mean()+h)/costs[:, li].mean())} for h in protocol['cost']['overhead_sensitivity_usd_per_task']]}
        if name in selections:
            selected = selections[name]
            row['model_counts'] = {m: int(np.sum(selected == j)) for j,m in enumerate(names) if np.any(selected == j)}
        summaries.append(row)
    summary = {'experiment': protocol['experiment_id'], 'kind': 'exploratory_public_agent_trajectory_outcome_replay_not_fresh_inference',
               'benchmark': protocol['benchmark'], 'tasks': len(ids), 'repositories': len(set(repos)),
               'models': metadata, 'primary_policy': 'cost_benefit_router_large_0.5',
               'primary_pair': protocol['primary_pair'], 'router_fit_seconds': fit_seconds,
               'actual_new_inference_spend_usd': 0, 'full_operational_cost_usd': None, 'subscription_credit_savings': None,
               'primary_result': next(r for r in summaries if r['policy']=='cost_benefit_router_large_0.5'),
               'pair_complementarity': {'both_solve': int(np.sum((quality[:,si]==1)&(quality[:,li]==1))),
                   'small_only': int(np.sum((quality[:,si]==1)&(quality[:,li]==0))),
                   'large_only': int(np.sum((quality[:,si]==0)&(quality[:,li]==1))),
                   'neither': int(np.sum((quality[:,si]==0)&(quality[:,li]==0)))},
               'prediction_metrics': {m:{'oof_brier':float(np.mean((p[:,j]-quality[:,j])**2)),
                       'oof_cost_mae_usd':float(np.mean(abs(predicted_cost[:,j]-costs[:,j])))} for j,m in enumerate(names)},
               'limits': ['Models ran upstream; this run fits routers and replays full task outcomes.',
                   'One historical attempt per model/task; stochastic rerun variability not measured.',
                   'Same harness version does not imply identical model reasoning effort, API settings or run date precision.',
                   'Upstream cost values are estimates, not independently audited invoices; environment/router costs excluded.',
                   'Folds share repositories. Bootstrap conditions on fixed OOF policies and does not retrain; only 12 repository clusters.',
                   'Portfolio and grid results are exploratory. Do not select a test-grid winner as confirmatory evidence.',
                   'No evidence about live conversation, distillation, Codex billing or present-day frontier models.',
                   'Small is a product tier here; GPT-5-mini parameter count and on-device feasibility are not established.'],
               'policies': summaries}
    output.mkdir(parents=True)
    dump(output/'summary.json', summary)
    dump(output/'sources.json', sources)
    dump(output/'folds.json', split_records)
    with (output/'task-records.jsonl').open('w') as stream:
        for i, task in enumerate(ids):
            row={'instance_id':task,'repository':repos[i],'fold':int(folds[i]),'problem_sha256':digest(texts[i].encode()),
                 'models':{m:{'resolved':bool(quality[i,j]),'source_estimated_cost_usd':float(costs[i,j]),
                      'api_calls':int(calls[i,j]),'oof_p_resolved':float(p[i,j]),'oof_predicted_cost_usd':float(predicted_cost[i,j])} for j,m in enumerate(names)},
                 'selected_models':{name:names[int(value[i])] for name,value in selections.items()}}
            stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,6))
    for name,label in [('cost_benefit_router','Learned cost/benefit router'),('benefit_router','Learned quality router'),('length_rule','Length rule'),('random_expected','Expected random routing')]:
        rr=[r for r in summaries if r['policy'].startswith(name+'_large_')]
        rr.sort(key=lambda r:r['estimated_inference_usd_per_task'])
        ax.plot([r['estimated_inference_usd_per_task'] for r in rr],[100*r['resolution_rate'] for r in rr],marker='o',label=label)
    rr=[r for r in summaries if r['policy'].startswith('portfolio_lambda_')]
    ax.scatter([r['estimated_inference_usd_per_task'] for r in rr],[100*r['resolution_rate'] for r in rr],marker='s',s=65,label='Ten-model utility portfolio')
    ax.set(xlabel='Upstream estimated inference USD per task (router/infra excluded)',ylabel='SWE-bench Verified resolved (%)',title='500-task public replay; five-fold held-out predictions')
    ax.legend(loc='lower right',fontsize=8);ax.grid(alpha=.25);fig.tight_layout()
    fig.savefig(output/'cost-quality.png',dpi=160);fig.savefig(output/'cost-quality.svg');plt.close(fig)
    dump(output/'run-manifest.json', {'completed_at_utc':datetime.now(timezone.utc).isoformat(),
        'protocol_sha256':digest(PROTOCOL.read_bytes()),'script_sha256':digest(Path(__file__).read_bytes()),
        'sources_sha256':digest((output/'sources.json').read_bytes()),'summary_sha256':digest((output/'summary.json').read_bytes()),
        'task_records_sha256':digest((output/'task-records.jsonl').read_bytes()),'fit_seconds':fit_seconds})
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['fetch','analyze','all'])
    parser.add_argument('--cache',type=Path,default=ROOT/'data/raw/swe-replay-001')
    parser.add_argument('--output',type=Path,default=ROOT/'results/swe-replay-001')
    args=parser.parse_args();protocol=load_protocol()
    if args.stage in ['fetch','all']:
        manifest=fetch(args.cache,protocol)
        print(json.dumps({'fetched_sources':len(manifest['sources'])}))
    if args.stage in ['analyze','all']:
        summary=analyze(args.cache,args.output,protocol)
        print(json.dumps({'tasks':summary['tasks'],'primary':summary['primary_result']},indent=2))


if __name__=='__main__':
    main()
