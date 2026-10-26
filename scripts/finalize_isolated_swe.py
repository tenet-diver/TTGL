#!/usr/bin/env python3
"""Collect owned-thread estimates and publish results from actual official grades."""
from __future__ import annotations
import argparse
import csv
import json
import os
import math
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark



def scenario_cost(manifest, prices):
    """Published Codex Standard token-rate scenario; never an observed bill."""
    if manifest.get('usage_accounting_issues') or not manifest.get('usage_by_model'):
        return None
    required = ('input_tokens', 'cached_input_tokens', 'output_tokens')
    if any(type(manifest.get('usage', {}).get(k)) is not int for k in required):
        return None
    total = 0.0
    observed = [0, 0, 0]
    for model, record in manifest['usage_by_model'].items():
        rate = prices['models'].get(model)
        counts = [record['usage'].get(k) for k in required]
        if not rate or any(type(n) is not int or n < 0 for n in counts):
            return None
        observed = [a+b for a,b in zip(observed, counts)]
        if counts[1] > counts[0]:
            raise ValueError('Cached input exceeds total native input')
        fields = ('input_per_million', 'cached_input_per_million', 'output_per_million')
        if any(type(rate.get(k)) not in (float, int) or not math.isfinite(rate[k]) or rate[k] < 0 for k in fields):
            raise ValueError('Invalid published token rate')
        total += ((counts[0]-counts[1])*rate[fields[0]] + counts[1]*rate[fields[1]] + counts[2]*rate[fields[2]])/1_000_000
    if observed != [manifest['usage'][k] for k in required]:
        raise ValueError('Per-model native counters do not reconcile to task totals')
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study, out = args.study_dir.resolve(), args.output.resolve()
    design, _ = benchmark.load_design(study)
    states = [study / 'runs' / a['arm'] / a['instance_id'] / 'state.json'
              for a in design['assignment_order']]
    if not all(path.is_file() for path in states):
        raise ValueError('Assigned states are missing; do not publish a completed study')
    if out.exists():
        raise ValueError('Choose a new final analysis directory')
    out.mkdir(parents=True)
    provider = out / 'provider-usage.json'
    command = [sys.executable, str(Path(__file__).with_name('collect_codex_usage.py')),
               '--output', str(provider), '--independent-roots']
    for state in states:
        command += ['--state', str(state)]
    result = subprocess.run(command, capture_output=True, text=True)
    (out / 'provider-collector.stdout.txt').write_text(result.stdout + result.stderr)
    if result.returncode not in (0, 2) or not provider.is_file():
        raise RuntimeError('Provider collector failed without a usable observation')
    portable = {arm: {key: os.path.relpath(Path(path) if Path(path).is_absolute() else study / path, out)
                       for key, path in rows.items()}
                for arm, rows in json.loads((study / 'grades.json').read_text()).items()}
    benchmark.write_new(out / 'grades-portable.json', portable)
    summary = benchmark.analyze(study, out / 'grades-portable.json', out / 'analysis',
                                provider_usage_path=provider)
    records = json.loads((out / 'analysis/records.json').read_text())
    if any(r['resolved'] is None for r in records):
        raise ValueError('Official grades are missing; results remain incomplete')
    environment = json.loads((study / 'environment.json').read_text())
    scenario_path = study / 'rate-scenario.json'
    if benchmark.digest(scenario_path) != environment['published_rate_scenario_sha256']:
        raise ValueError('Frozen token-rate scenario changed')
    rates = json.loads(scenario_path.read_text())
    scenario_records = [{**r, 'cost_usd': scenario_cost(json.loads((study / 'runs' / r['arm'] / r['task_id'] / 'manifest.json').read_text()), rates),
                         'cost_kind': rates['kind']} for r in records]
    scenario_summary = {'rates': rates, 'paired_savings': benchmark.paired_savings(scenario_records, design)}
    benchmark.write_new(out / 'published-rate-records.json', scenario_records)
    benchmark.write_new(out / 'published-rate-scenario.json', scenario_summary)
    totals = []
    for arm, quality in summary['arms'].items():
        rows = [r for r in records if r['arm'] == arm]
        patches = [json.loads((study / 'patches' / arm / (r['task_id'] + '.json')).read_text()) for r in rows]
        expert_requests = 0
        for row in rows:
            for line in (study / 'runs' / arm / row['task_id'] / 'events.jsonl').read_text().splitlines():
                event = json.loads(line)
                expert_requests += event.get('event') == 'request' and event.get('kind') == 'expert'
        totals.append({
            'condition': arm, 'assigned': quality['assigned'], 'resolved': quality['resolved'],
            'resolution_fraction': quality['resolved_per_assigned'],
            'input_tokens': sum(r['input_tokens'] for r in rows) if all(r['input_tokens'] is not None for r in rows) else None,
            'output_tokens': sum(r['output_tokens'] for r in rows) if all(r['output_tokens'] is not None for r in rows) else None,
            'expert_requests': expert_requests,
            'completed_expert_responses': quality['reported_expert_calls'],
            'mean_execution_seconds': quality['mean_wall_seconds'],
            'preparation_seconds': sum(p['preparation_seconds'] for p in patches),
            'api_equivalent_usd': quality['total_cost_usd'],
            'published_codex_standard_scenario_usd': (sum(r['cost_usd'] for r in scenario_records if r['arm'] == arm)
                if all(r['cost_usd'] is not None for r in scenario_records if r['arm'] == arm) else None),
        })
    with (out / 'condition-results.csv').open('x') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(totals[0]))
        writer.writeheader(); writer.writerows(totals)
    headers = ['task_id', *design['arms']]
    indexed = {(r['task_id'], r['arm']): r for r in records}
    with (out / 'task-results.csv').open('x') as stream:
        writer = csv.writer(stream); writer.writerow(headers)
        for key in design['task_ids']:
            writer.writerow([key, *[indexed[key, arm]['resolved'] for arm in design['arms']]])
    lines = ['# Metered isolated SWE-bench results', '',
        f"The study completed {len(records)} assignments on {len(design['task_ids'])} tasks across {len(design['arms'])} conditions. "
        'Outcomes come from the official pinned SWE-bench evaluator and are joined to exact exported patches.', '',
        '| Condition | Resolved | Input tokens | Output tokens | Expert requests | Published-rate scenario USD |',
        '|---|---:|---:|---:|---:|---:|']
    for row in totals:
        cost = row['published_codex_standard_scenario_usd']
        cost_label = f'{cost:.4f}' if cost is not None else 'unavailable'
        lines.append(f"| {row['condition']} | {row['resolved']}/{row['assigned']} | {row['input_tokens']} | {row['output_tokens']} | {row['expert_requests']} | {cost_label} |")
    lines += ['', '## Paired quality differences versus the large solo condition', '',
              '| Condition | Difference in percentage points | Conditional paired bootstrap 95% interval |',
              '|---|---:|---:|']
    for arm, row in summary['paired_differences'].items():
        low, high = row['bootstrap_percentile_95']
        lines.append(f"| {arm} | {100*row['quality_difference']:.1f} | {100*low:.1f} to {100*high:.1f} |")
    environment = json.loads((study / 'environment.json').read_text())
    executions = list(study.glob('grading/**/execution.json'))
    reuses = list(study.glob('grading/**/reuse.json'))
    lines += ['', f'Official evaluator invocations with retained execution records: {len(executions)}. '
              f'Exact-program report reuses: {len(reuses)}. Reuse is not an additional test execution.']
    lines += ['', '## Published-rate cost scenario', '',
        'Rates were verified and frozen before scored inference from the [official Enterprise Codex Standard-mode rate card]('
        + rates['source_url'] + '). They price native uncached input, cached input and output separately. '
        'This is a counterfactual token-rate scenario, not this account invoice, API bill or observed quota use. '
        'The signed-in Codex long-context exemption follows that rate card. See published-rate-scenario.json '
        'for paired cost-ratio uncertainty and published-rate-records.json for every assigned observation.', '',
        '| Condition | Estimated scenario saving versus large |', '|---|---:|']
    for arm, cost in scenario_summary['paired_savings'].items():
        saving = cost.get('estimated_savings_fraction')
        lines.append(f"| {arm} | {100*saving:.1f}% |" if saving is not None else f'| {arm} | unavailable |')
    lines += ['', '## Interpretation and accounting', '',
        'This is a small engineering panel of public historical tasks. It cannot establish a three-point '
        'noninferiority margin. The task bootstrap is conditional on this panel and may be degenerate; '
        'repositories and bug families can be correlated. No architectural novelty or open-weight/local-model result is claimed.', '',
        'Native input/output token totals are measured. Cached input is included within input, and reasoning '
        'is included within output. Input and output tokens have different economic weights; the table '
        'does not turn raw token reduction into dollar or quota savings. Router and expert turns are '
        'included in their assigned condition. Failed attempts remain in assigned-task accounting.', '',
        'Backend credit estimates are retained in provider-usage.json, including unavailable values. '
        'API-equivalent dollars remain null: API cache-write and request-level context pricing need a separately compatible meter. Provider '
        'estimates are not subscription invoices. Setup, independent controls, grading, hardware and '
        'subscription allocation require separate accounting. The registered joint cost/quality target '
        'is not established by these small-panel model-only measurements.', '',
        'Environment exclusions determined before scored inference: '
        + (', '.join(environment['excluded_environment_ids']) or 'none') + '.', '',
        'See analysis/records.json and analysis/summary.json for all assigned records, provenance, '
        'paired uncertainty and cost availability. grades-portable.json resolves archived reports relative to '
        'this directory so the analysis can be reproduced after relocating the checkout. The frozen design, environment, per-role journals, '
        'patches and original official grading logs are in the parent study directory.', '']
    (out / 'README.md').write_text('\n'.join(lines))
    benchmark.write_new(out / 'validation.json', {
        'status': 'completed_officially_graded_engineering_panel', 'assignments': len(records),
        'tasks': len(design['task_ids']), 'all_official_grades_joined_to_exact_patches': True,
        'powered_noninferiority_established': False,
        'full_deployment_savings_established': False,
        'design_sha256': benchmark.digest(study / 'design.json'),
        'environment_sha256': benchmark.digest(study / 'environment.json'),
        'grade_index_sha256': benchmark.digest(study / 'grades.json'),
        'portable_grade_index_sha256': benchmark.digest(out / 'grades-portable.json'),
        'provider_usage_sha256': benchmark.digest(provider),
        'published_rate_records_sha256': benchmark.digest(out / 'published-rate-records.json'),
        'published_rate_scenario_sha256': benchmark.digest(scenario_path),
        'grading_execution_records': len(executions), 'exact_program_grade_reuses': len(reuses),
    })
    print(json.dumps({'status': 'officially_graded', 'tasks': len(design['task_ids']),
                      'conditions': totals}), flush=True)


if __name__ == '__main__':
    main()
