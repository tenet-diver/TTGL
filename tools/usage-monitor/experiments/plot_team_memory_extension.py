#!/usr/bin/env python3
"""Standalone scientific SVG charts using reviewed Pygal; zero model calls."""
import argparse
import html
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

STYLES={
    'native':('Native','#0072B2'),'notebook':('Notebook','#E69F00'),
    'mcp_memory':('MCP memory','#009E73'),'mem0_luna':('Mem0 / Luna','#D55E00'),
    'graphiti_luna':('Graphiti / Luna','#CC79A7'),
    'smallville_luna':('Smallville / Luna','#56B4E9'),'searchable_logs':('Searchable logs','#444444'),
}


def static_svg(body):
    """Remove client configuration scripts; retain the library's geometry/data."""
    ET.register_namespace('','http://www.w3.org/2000/svg')
    ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
    root=ET.fromstring(body)
    for parent in root.iter():
        for child in list(parent):
            if child.tag.rsplit('}',1)[-1]=='script':parent.remove(child)
    for node in root.iter():
        for key,value in node.attrib.items():
            if key.rsplit('}',1)[-1] in ('href','src') and value.startswith(('http:','https:','//','file:')):
                raise ValueError('External figure asset is forbidden')
        if node.tag.rsplit('}',1)[-1]=='style' and node.text and ('@import' in node.text or 'url(http' in node.text):
            raise ValueError('External stylesheet/font is forbidden')
    return ET.tostring(root,encoding='unicode')


def plot(result,output):
    if result['state']!='complete' or result['completed']!=56 or result['planned']!=56:
        raise ValueError('Full registered comparison must finish before final figures')
    import pygal
    from pygal.style import Style
    output.mkdir(parents=True,exist_ok=True)
    panels={}
    for arm in STYLES:
        groups=sorted([g for g in result['groups'] if g['arm']==arm],key=lambda g:g['total_agent_capacity'])
        if [g['total_agent_capacity'] for g in groups]!=[1,2,4,8] or any(g['completed']!=g['planned'] or g['planned']!=2 for g in groups):
            raise ValueError('Missing complete two-library panel')
        panels[arm]=groups
    style=Style(background='white',plot_background='white',foreground='#333333',foreground_strong='#111111',
        foreground_subtle='#dddddd',colors=tuple(x[1] for x in STYLES.values()),font_family='sans-serif',
        label_font_size=15,major_label_font_size=15,legend_font_size=14,title_font_size=20)
    definitions=[
        ('quality','Prescribed-test resolution','Verified artifacts / 2 libraries',lambda g:g['successes']/2,(0,1.05)),
        ('normal-parents','Normal parent completion','Normal parents / 2 libraries',lambda g:g['normal_parents']/2,(0,1.05)),
        ('time','Mean coding-run end time','Seconds, including stopped cells',lambda g:g['mean_seconds'],None),
        ('cost-minima','Recorded inference scenario minima','Mean Standard credits; unknown totals may be higher',lambda g:g['mean_credit_lower_bound'],None),
        ('threads','Actual native coding participation','Mean distinct Sol coding threads',lambda g:g['mean_coding_threads'],(0,8.5)),
    ]
    figures=[]
    for name,title,y_label,metric,limits in definitions:
        graph=pygal.Line(width=1100,height=610,explicit_size=True,js=[],style=style,
            title='Memory-aware teams: '+title,x_title='Offered coding capacity (parent included)',y_title=y_label,
            legend_at_bottom=True,legend_at_bottom_columns=4,show_dots=True,dots_size=4,
            truncate_legend=-1,show_x_guides=False,show_y_guides=True,range=limits,
            disable_xml_declaration=True)
        graph.x_labels=['1','2','4','8']
        for arm,(label,color) in STYLES.items():
            graph.add(label,[dict(value=metric(g),label=f"{g['completed']} cells; {g['normal_parents']} normal parents; cost {'complete' if g['accounting_complete'] else 'lower bound'}") for g in panels[arm]])
        svg=static_svg(graph.render());filename='memory-aware-'+name+'.svg'
        (output/filename).write_text(svg+'\n');figures.append((title,svg,filename))
    caption=('Separately registered56-cell development comparison: two reused libraries, seven arms, capacities1/2/4/8, one attempt per cell. '
        'Agent/broker/algorithm sources and prompts fixed; dependency amendment after cell12 disclosed. '
        'Resolution and normal parent completion are separate. End-time averages include stopped parents and all in-agent memory work; '
        'they are not success-only solution times or full deployment latency. All cost points are recorded minima; '
        'missing usage has no measured upper bound and cannot be ranked as a known total. Sol and Luna inference included; '
        'local compute and research overhead additional. Actual threads exclude Luna maintenance. '
        'Coincident quality curves overlap without artificial offsets. No causal, cash, population speedup or generalization claim.')
    (output/'memory-aware-caption.txt').write_text(caption+'\n')
    sections=''.join('<section><h2>'+html.escape(title)+'</h2>'+svg+'</section>' for title,svg,name in figures)
    (output/'memory-aware-figures.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Memory-aware team study</title><style>body{font:16px sans-serif;max-width:1150px;margin:2rem auto;padding:1rem}svg{width:100%;height:auto}section{break-inside:avoid;margin:2rem 0}p{line-height:1.5}</style><h1>Memory-aware coding teams</h1><p>'+html.escape(caption)+'</p>'+sections+'</html>\n')
    (output/'memory-aware-plot-provenance.json').write_text(json.dumps(dict(renderer='Pygal',version=pygal.__version__,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        canonical_result_sha256=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        source_cells=56,scripts_removed=True,external_assets=False,model_calls=0,
        svg_sha256={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for title,svg,name in figures}),indent=2)+'\n')
    return [name for title,svg,name in figures]


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(dict(figures=plot(json.loads(a.results.read_text()),a.output),remote_model_calls=0)))
