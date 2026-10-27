#!/usr/bin/env python3
"""Plot completed prompt studies with their own matched standalone controls."""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark, frontier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def summarize(path):
    rows = json.loads(path.read_text())
    result = {}
    for arm in sorted({r['arm'] for r in rows}):
        selected = [r for r in rows if r['arm'] == arm]
        ids = [r['task_id'] for r in selected]
        if len(set(ids)) != len(ids) or not ids:
            raise ValueError('Duplicate or empty assigned panel')
        if any(type(r['resolved']) is not bool or type(r['cost_usd']) not in (int, float)
               or r['cost_usd'] <= 0 for r in selected):
            raise ValueError('Require observed grades and positive scenario costs')
        result[arm] = {'tasks': sorted(ids), 'n': len(ids),
                       'resolved': sum(r['resolved'] for r in selected),
                       'cost_per_task': sum(r['cost_usd'] for r in selected)/len(ids),
                       'expert_calls': sum(r['expert_calls'] for r in selected)}
        if arm != 'large':
            frontier.compare(rows, policy=arm)  # Reject incomplete matched pairs.
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', action='append', required=True, help='Label=analysis directory')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    panels, provenance = [], []
    for spec in args.study:
        label, directory = spec.split('=', 1)
        path = Path(directory)/'published-rate-records.json'
        rows = summarize(path)
        panels.append((label, rows))
        provenance.append({'label': label, 'records': str(path), 'sha256': benchmark.digest(path), 'points': rows})
    args.output_dir.mkdir(parents=True, exist_ok=False)
    columns = min(2, len(panels))
    panel_rows = math.ceil(len(panels)/columns)
    fig, axes = plt.subplots(panel_rows, columns, figsize=(6*columns, 6*panel_rows), squeeze=False)
    labels = {'small':'Luna alone', 'large':'Sol alone', 'personal':'Luna + Sol access',
              'oneway':'One-way help', 'reset_expert':'Fresh expert', 'precall_router':'Pre-task router'}
    colors = {'small':'#2875b2', 'large':'#292929', 'personal':'#d26c18', 'oneway':'#8c5c9c',
              'reset_expert':'#b34856', 'precall_router':'#448b83'}
    for ax, (label, rows) in zip(axes.flat, panels):
        ref = rows['large']
        target_x = ref['cost_per_task']*.05
        target_y = 100*ref['resolved']/ref['n']*.95
        ax.axvspan(target_x/100, target_x, ymin=target_y/105, color='#d9eedf', alpha=.9)
        ax.axvline(target_x, color='#38764b', ls='--', lw=1)
        ax.axhline(target_y, color='#38764b', ls='--', lw=1)
        for arm, row in rows.items():
            ax.scatter(row['cost_per_task'], 100*row['resolved']/row['n'], s=65,
                       color=colors[arm], marker='s' if arm=='large' else 'o',
                       label=f"{labels[arm]}: {row['resolved']}/{row['n']}; {row['expert_calls']} help calls")
        ax.set_xscale('log')
        ax.set_xlim(min(target_x*.6, min(r['cost_per_task'] for r in rows.values())*.6),
                    max(r['cost_per_task'] for r in rows.values())*1.7)
        ax.set_ylim(0, 105)
        ax.set_title(label)
        ax.set_xlabel('Model-cost scenario (USD / assigned task; log scale)')
        ax.set_ylabel('Tasks resolved (%)')
        ax.grid(alpha=.2)
        ax.legend(loc='upper center', bbox_to_anchor=(.5, -.22), fontsize=8, frameon=False)
    fig.suptitle('Luna / Sol cost–performance combinations', fontsize=15)
    fig.text(.5, .015, 'Green region: ≥95% Sol accuracy at ≤5% Sol cost, within each panel. No interpolation between policies.\n'
             'Published token-rate scenarios, not invoices. Development panels reuse four tasks; not independent held-out evidence.',
             ha='center', fontsize=9)
    for ax in list(axes.flat)[len(panels):]:
        ax.set_visible(False)
    fig.subplots_adjust(bottom=.20, top=.93, wspace=.25, hspace=.85)
    for suffix in ('png', 'svg'):
        fig.savefig(args.output_dir/('combinations.'+suffix), dpi=180, bbox_inches='tight')
    plt.close(fig)
    benchmark.write_new(args.output_dir/'provenance.json', {'studies': provenance,
        'script_sha256': benchmark.digest(Path(__file__)), 'matplotlib_version': matplotlib.__version__,
        'interpretation': 'Separate descriptive panels; repeated controls and different panels are not pooled.'})


if __name__ == '__main__':
    main()
