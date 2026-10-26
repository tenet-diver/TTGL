#!/usr/bin/env python3
"""Plot actual matched live outcomes under an explicitly labelled cost scenario."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark, frontier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--records', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
args = parser.parse_args()
records = json.loads(args.records.read_text())
arms = sorted({r['arm'] for r in records})
comparisons = {arm: frontier.compare(records, policy=arm) for arm in arms if arm != 'large'}
if any(r['cost_ratio'] is None or r['accuracy_retention_ratio'] is None for r in comparisons.values()):
    raise ValueError('Missing paired cost/quality values; do not chart unknowns as zero')
args.output_dir.mkdir(parents=True, exist_ok=False)
y_top = max(110,max(100*r['accuracy_retention_ratio'] for r in comparisons.values())+5)
fig, ax = plt.subplots(figsize=(8, 5.5))
ax.axvspan(.001, 5, ymin=95/y_top, ymax=1, color='#d9eedf', alpha=.8)
ax.axhline(95, color='#38764b', linestyle='--', linewidth=1)
ax.axvline(5, color='#38764b', linestyle='--', linewidth=1)
colors = {'small':'#2875b2','personal':'#d26c18','oneway':'#8c5c9c',
          'reset_expert':'#b34856','precall_router':'#448b83'}
for arm, row in comparisons.items():
    x, y = 100*row['cost_ratio'], 100*row['accuracy_retention_ratio']
    if x <= 0:
        raise ValueError('A log cost chart requires positive measured scenario cost')
    ax.scatter(x, y, s=65, color=colors.get(arm),
               label=f"{arm}: {row['policy_resolved']}/{row['paired_tasks']}; cost {x:.1f}%")
reference = [r for r in records if r['arm']=='large']
ax.scatter(100,100,s=75,color='#292929',marker='s',
           label=f"large: {sum(r['resolved'] for r in reference)}/{len(reference)}; cost 100%")
ax.set_xscale('log')
ax.set_xlim(min(.5,min(50*r['cost_ratio'] for r in comparisons.values())),
            max(120, max(100*r['cost_ratio'] for r in comparisons.values())*1.2))
ax.set_ylim(0,y_top)
ax.set_xticks([1,5,10,25,50,100], ['1','5','10','25','50','100'])
ax.set_xlabel('Published token-rate scenario cost (% of matched Sol-only; log scale)')
ax.set_ylabel('Task accuracy retained (% of matched Sol-only)')
ax.set_title('Matched live outcomes and the 95% saving / 95% retention target')
ax.grid(alpha=.2)
ax.legend(loc='lower center',bbox_to_anchor=(.5,-.39),ncol=2,frameon=False,fontsize=9)
fig.text(.5,.01,'Point estimates on public tasks; development and held-out panels must be interpreted separately.\nToken-rate scenario excludes deployment overhead and is not an observed invoice.',ha='center',fontsize=8)
fig.subplots_adjust(bottom=.34,left=.11,right=.97,top=.90)
for suffix in ('png','svg'):
    fig.savefig(args.output_dir/('frontier.'+suffix),dpi=220,bbox_inches='tight')
plt.close(fig)
benchmark.write_new(args.output_dir/'provenance.json',{
    'records_sha256':benchmark.digest(args.records),
    'script_sha256':benchmark.digest(Path(__file__)),
    'comparisons':comparisons,
    'cost_definition':'Published Codex Standard token-rate scenario; not observed billing or full deployment cost'})
