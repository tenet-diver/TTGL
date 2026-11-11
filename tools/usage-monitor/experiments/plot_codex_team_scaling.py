#!/usr/bin/env python3
"""Standalone scientific figures; read summaries only, never invoke models."""
import argparse
import json
from pathlib import Path


def plot(source, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d=json.loads(source.read_text());output.mkdir(parents=True,exist_ok=False)
    colors={'native':'#334155','notebook':'#0072B2','mcp_memory':'#D55E00'}
    names={'native':'Native Codex','notebook':'Shared notebook','mcp_memory':'MCP memory'}
    capacities=[1,2,4,8];tasks=['simpy','tinydb']
    fig,axes=plt.subplots(2,3,figsize=(13,7.4),layout='constrained')
    for row,task in enumerate(tasks):
        for condition in colors:
            cells=sorted([x for x in d['cells'] if x['task']==task and x['condition']==condition],key=lambda x:x['total_agent_capacity'])
            if not cells:continue
            xs=[capacities.index(x['total_agent_capacity']) for x in cells]
            quality=[int(x['grade']['passed'] and x['grade']['artifact_policy_clean']) for x in cells]
            offset={'native':-.055,'notebook':0,'mcp_memory':.055}[condition]
            axes[row,0].scatter([x+offset for x in xs],quality,color=colors[condition],label=names[condition],s=45)
            axes[row,1].plot(xs,[x['wall_seconds'] for x in cells],'-o',color=colors[condition],label=names[condition])
            for x,cell in zip(xs,cells):
                if cell.get('parent_native_status','completed')!='completed':
                    axes[row,1].scatter(x,cell['wall_seconds'],marker='x',color='#b91c1c',s=90,zorder=5,label='Parent stream failed')
                complete=cell['inference_accounting_complete']
                axes[row,2].scatter(x+offset,cell['standard_credit_lower_bound'],marker='o' if complete else '^',
                    facecolors=colors[condition] if complete else 'none',edgecolors=colors[condition],s=48,linewidths=1.4)
                if cell['total_agent_capacity']==8:
                    axes[row,1].annotate(' '+str(cell['actual_threads'])+' threads',
                        (x,cell['wall_seconds']),fontsize=7,color=colors[condition])
        axes[row,0].set(ylabel=task+' — verified resolution',ylim=(-.1,1.15),yticks=[0,1],yticklabels=['Fail','Pass'])
        axes[row,1].set(ylabel='Attempt time (seconds)',ylim=(0,None))
        axes[row,2].set(ylabel='Standard-credit scenario\nOpen triangles are lower bounds',ylim=(0,None))
        for ax in axes[row]:
            ax.set(xticks=range(4),xticklabels=capacities,xlim=(-.2,3.8),xlabel='Allowed total agents (parent included)')
            ax.grid(alpha=.2)
            ax.spines[['top','right']].set_visible(False)
    status='Completed' if d['complete'] else 'Interim'
    fig.suptitle(f'{status} native Codex knowledge pilot — {d["completed"]}/{d["planned"]} assignments\nTwo development libraries; one attempt per cell',fontsize=13)
    handles,labels=axes[0,1].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=3,frameon=False)
    for extension in ('svg','pdf','png'):
        fig.savefig(output/('scaling.'+extension),dpi=180,bbox_inches='tight')
    plt.close(fig)
    (output/'caption.txt').write_text(
        'Independent source-only prescribed-test replay. Codex0.167.0, GPT6.1Sol low reasoning. '
        'Each point is one attempt; no population uncertainty is estimated from two repositories. '
        'Thread labels count distinct owned native threads, not necessarily simultaneous workers. '
        'A red cross marks time to a failed parent turn whose sealed artifact nevertheless passed independent replay; it is not a successful final turn. '
        'Open cost triangles show completed-response lower bounds; missing interrupted-stream usage has no upper estimate. '
        'Cost scenarios are not subscription cash charges. No total-cost ranking is supported for incomplete cells.\n')
    print('Saved SVG, PDF and PNG figures with explicit incomplete-cost markers.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();plot(a.analysis,a.output)
