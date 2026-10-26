#!/usr/bin/env python3
"""Produce transparent additional comparisons from the frozen replay records.

MiniMax as the added reference was chosen AFTER viewing all single-model rows.
The original primary analysis and manifest are retained unchanged.
"""
from __future__ import annotations
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
import numpy as np
import swe_public_replay as replay


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,default=replay.ROOT/'results/swe-replay-001')
    args=parser.parse_args();root=args.results
    report=json.loads((root/'summary.json').read_text())
    rows=[json.loads(x) for x in (root/'task-records.jsonl').read_text().splitlines()]
    repos=[r['repository'] for r in rows]
    task_boot=replay.bootstrap_indices(repos,2000,False)
    cluster_boot=replay.bootstrap_indices(repos,2000,True)
    def model(m):
        return np.asarray([r['models'][m]['resolved'] for r in rows],dtype=float),np.asarray([r['models'][m]['source_estimated_cost_usd'] for r in rows])
    def policy(p):
        return np.asarray([r['models'][r['selected_models'][p]]['resolved'] for r in rows],dtype=float),np.asarray([r['models'][r['selected_models'][p]]['source_estimated_cost_usd'] for r in rows])
    def compare(q,c,bq,bc):
        return {'resolution_difference':float(q.mean()-bq.mean()),'cost_ratio':float(c.sum()/bc.sum()),
                'estimated_inference_saving_fraction':float(1-c.sum()/bc.sum()),
                'task_bootstrap':replay.interval_summary(q,c,bq,bc,task_boot),
                'repository_cluster_bootstrap':replay.interval_summary(q,c,bq,bc,cluster_boot)}
    sq,sc=model('gpt_5_mini');lq,lc=model('gpt_5_2_high');mq,mc=model('minimax_2_5_high')
    pq,pc=policy('cost_benefit_router_large_0.5')
    additional={'status':'additional_descriptive_comparisons_after_initial_analysis',
       'reference_selection_note':'Every single model was a planned baseline. MiniMax is singled out here after observing that it was cheaper and more accurate than the preselected GPT-5.2 baseline. No router or grid value was refitted.',
       'primary_vs_expected_random_half':compare(pq,pc,(sq+lq)/2,(sc+lc)/2),
       'primary_vs_expected_random_note':'Random baseline is analytic expected selection, not a newly executed randomized model trial. Intervals resample tasks; random allocation variance is not included.',
       'portfolio_vs_minimax':{p:compare(*policy(p),mq,mc) for p in rows[0]['selected_models'] if p.startswith(('portfolio_lambda_','open_weight_portfolio_lambda_'))}}
    additional['literal_zero_cost_records'] = [
        {'instance_id':r['instance_id'], 'model':m, 'api_calls':v['api_calls'],
         'resolved':v['resolved'], 'source_estimated_cost_usd':v['source_estimated_cost_usd'],
         'selected_by':[p for p,selected in r['selected_models'].items() if selected == m],
         'interpretation':'Explicit upstream zero, not an imputed missing value. Billing completeness unverified; do not infer free inference.'}
        for r in rows for m,v in r['models'].items() if v['source_estimated_cost_usd'] == 0]
    replay.dump(root/'additional-comparisons.json',additional)
    software={x:importlib.metadata.version(x) for x in ['numpy','scipy','scikit-learn','matplotlib']}
    replay.dump(root/'software-versions.json',software)
    columns=['policy','tasks','resolved','resolution_rate','estimated_inference_total_usd','estimated_inference_usd_per_task','estimated_inference_usd_per_resolved_task','inference_saving_vs_large_fraction','resolution_difference_vs_large','large_model_fraction','nondeployable_oracle']
    with (root/'policy-table.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        writer.writerows({k:r[k] for k in columns} for r in report['policies'])
    chosen=['always_gpt_5_mini','always_gpt_5_2_high','random_expected_large_0.5','cost_benefit_router_large_0.5','always_minimax_2_5_high','portfolio_lambda_0.25','NONDEPLOYABLE_pair_outcome_cost_oracle','NONDEPLOYABLE_portfolio_outcome_cost_oracle']
    table=[]
    for name in chosen:
        r=next(r for r in report['policies'] if r['policy']==name)
        table.append(f"| `{name}` | {100*r['resolution_rate']:.1f}% | ${r['estimated_inference_usd_per_task']:.4f} | {100*r['inference_saving_vs_large_fraction']:.1f}% |")
    pair=additional['portfolio_vs_minimax']['portfolio_lambda_0.25']
    random=additional['primary_vs_expected_random_half']
    text='''# SWE-bench Verified: 500-task public replay

This experiment **was executed**: success and cost predictors for ten models were fitted in five held-out task folds and routed the published outcomes of 500 SWE-bench Verified tasks (5,000 upstream model attempts). It did **not** execute 5,000 new model attempts. The separate live Codex experiment remains a different artifact.

The fixed primary cost/benefit router saved **46.1% of source-estimated inference cost**, but resolved **64.2%**, versus **72.8%** for GPT-5.2 (high): an **8.6 percentage-point loss**. It fails the proposed 3-point noninferiority criterion. This is evidence of a cost-quality tradeoff, not evidence that the proposed conversational system preserves quality.

| Policy | Resolved | Estimated inference/task | Saving vs GPT-5.2 |
|---|---:|---:|---:|
'''+ '\n'.join(table)+'''

All dollars are **historical source-reported estimated API inference costs**. They exclude router compute, repository environments, grading, energy and subscription allocation; they are not invoices or current quotes. New paid model-inference spend for this analysis was $0. Full operational cost and Codex subscription savings remain unknown. Added-cost sensitivities are recorded for $0, $0.001, $0.01 and $0.05 per task, without pretending these hypothetical overheads were measured.

## What the comparisons actually show

The primary router does not improve on expected random half allocation: its resolution difference is '''+f"{100*random['resolution_difference']:.1f} points (task-bootstrap 95% CI {100*random['task_bootstrap']['paired_resolution_difference_ci95'][0]:.2f} to {100*random['task_bootstrap']['paired_resolution_difference_ci95'][1]:.2f}), with {100*random['estimated_inference_saving_fraction']:.1f}% lower estimated cost."+'''

The ten-model portfolio has attractive outcomes relative to GPT-5.2, but **MiniMax 2.5 alone is the essential control**: 75.8% at $0.0733/task. The portfolio at utility weight 0.25 resolves 76.2% at $0.1154/task, '''+f"{100*pair['resolution_difference']:.1f} points more, but costs {pair['cost_ratio']:.2f} times MiniMax alone. Its paired quality CI against MiniMax is {100*pair['task_bootstrap']['paired_resolution_difference_ci95'][0]:.2f} to {100*pair['task_bootstrap']['paired_resolution_difference_ci95'][1]:.2f} points."+''' Thus this replay does not establish that routing adds value over the strongest cheap single model. That comparator was selected for discussion after inspecting the planned single-model table; the extra comparison is explicitly labelled post-analysis.

The full declared utility grid is retained. No chosen grid point is presented as a confirmatory win. Open-weight portfolio variants use the upstream `os_model` metadata classification, which is not an independent license audit or a claim that these models run on a consumer laptop. GPT-5-mini is a smaller **product tier**, with no parameter-count claim.

Small/large complementarity exists: 262 tasks solved by both, 19 only by GPT-5-mini, 102 only by GPT-5.2, and 117 by neither. The pair oracle reaches 76.6%, and the ten-model oracle 87.8%. These oracles inspect the **actual test outcomes and actual task costs**, select the cheapest successful model, and are impossible deployment baselines. They bound the value of perfect selection, not the expected benefit of conversation.

## Method and uncertainty

The protocol was fixed before model fitting, after public aggregate accuracies/costs had been inspected. It is an exploratory secondary analysis, not prospective preregistration. The primary pair and 50% large-model quota were fixed before fitting. Feature extraction uses only issue text, its length and repository name. Logistic regression predicts success; ridge regression predicts log-transformed cost. Each prediction uses four folds and each quota is ranked **within its own held-out fold**, so held-out labels/costs do not influence that fold's choices through global ranking. No gold patch, test patch, trajectory or API-call count enters routing.

The same mini-SWE-agent 2.0.0 harness version and 2026-02-17 submission family were used. Model effort and API parameters may differ; source metadata for GPT-5.2 says high, while GPT-5-mini does not declare high effort. The study compares the published configurations, not matched weights or all current October-2026 frontier products. Source cost/accuracy aggregates reconcile exactly (within numerical tolerance) with the 500 per-instance records for every model. No missing grade or cost is replaced by zero.

We report 2,000 paired task-bootstrap draws and paired repository-cluster sensitivity over 12 repositories, conditional on the fixed fitted policies and published single attempts. The primary resolution difference CI is −11.605 to −5.600 points, and the cost-ratio CI is 0.4860–0.5917; the cluster sensitivity leads to the same failed quality conclusion. These are not intervals for fresh-run stochasticity or router retraining. Folds share repositories, the benchmark is public/historical, and contamination remains possible. Neither unseen-repository transfer nor conversation is measured. Router issue text comes from the pinned official task distribution joined by instance ID; byte identity with each upstream model's original prompt was not independently established.

## Reproduce and inspect

```bash
bash scripts/setup_research.sh
/workspace/.tools/ttgl-research/bin/python scripts/swe_public_replay.py fetch
/workspace/.tools/ttgl-research/bin/python scripts/swe_public_replay.py analyze --output /tmp/ttgl-swe-replay-reproduction
/workspace/.tools/ttgl-research/bin/python scripts/swe_replay_report.py --results /tmp/ttgl-swe-replay-reproduction
```

Use the Python environment path created by setup if your checkout is not under `/workspace`. `analyze` refuses an existing output directory. It validates every source SHA-256 and the frozen protocol before fitting. Raw problem statements/submissions are an ignored local cache because the two distribution repositories did not expose a top-level license at the inspected commit. Numerical results, source URLs/hashes, and retrieval code are retained; review upstream terms before redistributing raw text.

- `summary.json`: every policy, confidence interval, sensitivity and interpretive limit.
- `task-records.jsonl`: all 500 task-level public outcomes/costs, held-out predictions and choices.
- `additional-comparisons.json`: primary versus random; all portfolio grid points versus MiniMax, transparently added after initial analysis.
- `folds.json`: exact training/test allocations.
- `policy-table.csv`: compact table for all declared policies.
- `sources.json`: 522 pinned sources with hashes, including all 500 official problem statements.
- `cost-quality.png` / `.svg`: standard exported cost-quality plot.
- `run-manifest.json`: frozen protocol, code and result hashes for the original analysis.
- `software-versions.json`: statistical package versions.

Primary source: [SWE-bench/experiments at 40f164d](https://github.com/SWE-bench/experiments/tree/40f164d5b8f1d249bf95a6df8b74b577fd8e519d/evaluation/verified). Issue text: [official swe-bench-tasks at 3d07b46](https://github.com/SWE-bench/swe-bench-tasks/tree/3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d).
'''
    text += '''
## Explicit upstream zero-cost records

Gemini 3 Flash has two literal source cost values of $0: `django__django-15731` and `django__django-15814`. Both report one API call and an unresolved task. These are retained published values, not imputed missingness, but their billing completeness is unverified. They must not be interpreted as free inference. They affect the standalone Gemini row and some low-penalty portfolio points; the primary pair, portfolio weight 0.25, and both reported oracles select different models for these rows. `additional-comparisons.json` lists every affected policy. No zero-cost claim is used to infer a subscriber's plan usage.

Pinned repository-root license inspection is recorded in `license-checks.json`; it found no explicit top-level license in either distribution repository. Model open-weight labels come from submission metadata and are not a license audit.
'''
    (root/'README.md').write_text(text)
    replay.dump(root/'additional-analysis-manifest.json', {
        'report_script_sha256':replay.digest(Path(__file__).read_bytes()),
        'original_summary_sha256':replay.digest((root/'summary.json').read_bytes()),
        'original_records_sha256':replay.digest((root/'task-records.jsonl').read_bytes()),
        'additional_comparisons_sha256':replay.digest((root/'additional-comparisons.json').read_bytes()),
        'readme_sha256':replay.digest((root/'README.md').read_bytes()),
        'status':'additional comparisons; no new fit or selection'})
    print(json.dumps({'primary_vs_random':random,'portfolio_025_vs_minimax':pair},indent=2))


if __name__=='__main__':
    main()
