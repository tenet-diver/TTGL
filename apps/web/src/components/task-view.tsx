'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { AnalysisCard } from './analysis-card';
import { DataTable } from './data-table';
import { MutationDialog } from './mutation-dialog';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { format } from '@/lib/format';
import { categoryColors, type Row, type NativeEvent } from '@/lib/types';
interface Detail {
    task: Row;
    metrics: Record<string, number | null>;
    turns: Row[];
    groups: Row[];
    notes: Row[];
    analysis: Row | null;
    loops: Row[];
    images: Row[];
    jobs: Row[];
    events: Row[];
    duration: number | null;
    complete: boolean;
}
export function TaskView({ data: d }: {
    data: Detail;
}) {
    const params = useSearchParams(), [ids, setIds] = useState(params.get('steps') || ''), [image, setImage] = useState<Row | null>(null);
    const id = d.task.id;
    const checks = d.notes.filter(n => n.kind === 'validation'), changes = d.notes.filter(n => n.kind === 'change');
    const run = [...d.events].filter(e => e.at), times = run.map(e => Date.parse(String(e.at))), start = Math.min(...times), end = Math.max(...times), span = Math.max(1, end - start);
    return <><header className="page-header"><div><p className="eyebrow"><Link href="/tasks">Task activity /</Link></p><h1 className="task-title">{String(d.task.title)}</h1><p className="page-description">{d.turns.length} native turns · {String(d.task.status)} · {d.complete ? 'Explained' : 'Unclassified'}</p></div><MutationDialog action="evidence" title="Record evidence" values={{ task_id: id }} fields={[{ key: 'kind', label: 'Evidence kind', options: ['change', 'validation', 'visual_reference', 'intervention'].map(value => ({ value, label: value })) }, { key: 'title', label: 'Title', required: true }, { key: 'detail', label: 'Evidence', type: 'textarea' }, { key: 'outcome', label: 'Outcome', options: ['unknown', 'passed', 'failed', 'confirmed', 'not_applicable'].map(value => ({ value, label: value })) }, { key: 'reference', label: 'Source URL' }]}><Button size="sm" variant="outline">Record evidence</Button></MutationDialog></header>
 <AnalysisCard title="Story" description="What was asked, what changed, how it was checked and what is still open" className="task-story-card"><dl className="task-story"><dt>Asked</dt><dd>{String(d.task.goal || d.task.title)}</dd><dt>Changed</dt><dd>{changes.length ? changes.map(n => String(n.title)).join(' · ') : 'No explicit change evidence recorded.'}</dd><dt>Checked</dt><dd>{checks.length ? checks.map(n => String(n.title) + ' — ' + n.outcome).join(' · ') : 'No check evidence recorded.'}</dd><dt>Open</dt><dd>{String(d.task.outcome || 'Acceptance remains unverified.')}</dd></dl><p className="eyebrow">Timeline · click a phase to see its steps</p><div className="phase-track">{d.groups.map(g => <button key={g.id} title={String(g.title)} style={{ flex: Math.max(1, (g.event_ids as string[]).length), background: categoryColors[String(g.category).toLowerCase()] || '#999' }} onClick={() => setIds((g.event_ids as string[]).join(','))}/>)}{!d.groups.length && <p className="section-note">No interpreted phases. Analyze this task to group its native steps.</p>}</div><div className="chart-legend">{[...new Set(d.groups.map(g => String(g.category)))].map(name => <span key={name}><i style={{ background: categoryColors[name] || '#999' }}/>{name}</span>)}</div></AnalysisCard>
 <AnalysisCard title="Evidence" description="Recorded checks, retained screenshots and the last interpretation"><div className="evidence-grid"><section><h3>Checks</h3>{checks.length ? checks.map(n => <p key={n.id}>{String(n.title)} · {String(n.outcome)}<br />{String(n.detail)}</p>) : <p>No test, build or lint evidence recorded.</p>}</section><section><h3>Screenshots</h3><div className="screenshot-grid">{d.images.map(i => <button key={i.id} onClick={() => setImage(i)}><img src={'/api/images/' + encodeURIComponent(i.id)} alt={'Retained screenshot for ' + i.event_id} loading="lazy"/><small>{String(i.event_id)}</small></button>)}</div>{!d.images.length && <p>No retained raster screenshots.</p>}</section><section><h3>Interpretation</h3><p>{String(d.analysis?.summary || 'No analysis recorded.')}</p><p className="section-note">Model interpretation is separate from acceptance evidence.</p></section></div></AnalysisCard>
 <div className="metric-strip task-metrics">{[['Cost', d.metrics.cost, 'money'], ['Duration', d.duration, 'duration'], ['API calls', d.metrics.responses], ['Tool calls', d.metrics.tools], ['Tokens', d.metrics.tokens, 'tokens'], ['Errors', d.metrics.errors]].map(([label, value, type]) => <div className="metric" key={String(label)}><span>{label}</span><strong>{format(value, type as 'money')}</strong></div>)}</div>
 <AnalysisCard title="Prompt" defaultOpen={false}><DataTable id="task-prompts" rows={d.turns.map(t => ({ ...t, id: String(t.turn_key) }))} columns={[{ key: 'prompt', label: 'Prompt' }, { key: 'started_at', label: 'Started', type: 'date' }]}/></AnalysisCard>
 <AnalysisCard title="Outcome"><div className="evidence-grid"><section><h3>Did it work?</h3><p>{String(d.task.outcome || 'Unknown; no acceptance recorded.')}</p></section><section><h3>Where did it get stuck?</h3>{d.loops.length ? d.loops.map((loop, i) => <Button key={i} variant="link" onClick={() => setIds((loop.ids as string[]).join(','))}>{String(loop.detail)}</Button>) : <p>No repeated failed-call loop found.</p>}</section><section><h3>What did it change?</h3>{changes.map(n => <p key={n.id}>{String(n.title)}<br />{String(n.detail)}</p>)}<Link href="/outcomes">All outcomes →</Link></section></div></AnalysisCard>
 <AnalysisCard title="Subtasks" description="The analysis worker groups retained native steps with evidence references."><MutationDialog action="analyze" title="Explain task" description="Queue one explicit analysis. Existing active, uncertain or completed attempts are retained without automatic retries." values={{ task_id: id }}><Button size="sm">Explain task</Button></MutationDialog><DataTable id="task-subtasks" rows={d.groups} columns={[{ key: 'title', label: 'Subtask' }, { key: 'category', label: 'Category' }, { key: 'summary', label: 'Summary' }, { key: 'confidence', label: 'Confidence', type: 'percent' }]}/>{d.jobs.length > 0 && <DataTable id="task-analysis-jobs" rows={d.jobs} columns={[{ key: 'status', label: 'Analysis status' }, { key: 'model', label: 'Model' }, { key: 'error', label: 'Error' }]} compact/>}</AnalysisCard>
 <div className="dashboard-grid task-runtime-grid"><AnalysisCard title="Step timeline"><div className="native-timeline">{run.slice(0, 300).map(e => <button key={e.id} title={String(e.name) + ' · ' + format(e.runtime, 'duration')} onClick={() => setIds(e.id)}><span>{String(e.model || e.name)}</span><div><i style={{ left: (Date.parse(String(e.at)) - start) / span * 100 + '%', width: Math.max(.3, Number(e.runtime || 0) * 1000 / span * 100) + '%', background: categoryColors[String(e.category)] || '#52a8ff' }}/></div><small>{format(e.runtime, 'duration')}</small></button>)}</div></AnalysisCard><AnalysisCard title="Tools"><DataTable id="task-tools" kind="tools" extra={{ task: id }}/></AnalysisCard></div>
 <AnalysisCard title="Steps" className="span-full">{ids && <Button variant="outline" size="sm" onClick={() => setIds('')}>Clear phase / step filter</Button>}<DataTable id="task-steps" kind="steps" extra={{ task: id, ...(ids ? { ids } : {}) }}/></AnalysisCard>
 <Dialog open={Boolean(image)} onOpenChange={open => !open && setImage(null)}><DialogContent className="evidence-dialog"><DialogHeader><DialogTitle>Retained screenshot</DialogTitle><DialogDescription>{String(image?.event_id || '')}</DialogDescription></DialogHeader>{image && <img className="image-preview" src={'/api/images/' + encodeURIComponent(image.id)} alt="Retained task evidence"/>}</DialogContent></Dialog>
 </>;
}
