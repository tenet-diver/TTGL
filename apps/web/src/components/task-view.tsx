'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { operationIntervals } from '@/lib/timeline';
import { AnalysisCard } from './analysis-card';
import { DataTable } from './data-table';
import { MutationDialog } from './mutation-dialog';
import { Button } from './ui/button';
import { SemanticBadge } from './semantic-badge';
import { colorFor } from '@/lib/semantic-colors';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { format } from '@/lib/format';
import { type Row } from '@/lib/types';
interface Detail {
    task: Row;
    selected_subtask: Row | null;
    relations: Row[];
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
    const router = useRouter(), params = useSearchParams(), [ids, setIds] = useState(params.get('steps') || ''), [image, setImage] = useState<Row | null>(null);
    const id = d.task.id, selected = d.selected_subtask, scope = { task: id, ...(selected ? { subtask: selected.id } : {}) };
    const checks = d.notes.filter(n => n.kind === 'validation'), changes = d.notes.filter(n => n.kind === 'change');
    const run = operationIntervals(d.events), times = run.flatMap(e => [e.start, e.end]), start = times.length ? Math.min(...times) : 0, end = times.length ? Math.max(...times) : 0, span = Math.max(1, end - start), byId = new Map(run.map(e => [e.id, e]));
    const result = (d.analysis?.result || {}) as Record<string, unknown>;
    const pending = d.jobs.some(j => ['queued', 'running'].includes(String(j.status)));
    useEffect(() => {
        if (!pending)
            return;
        const timer = setInterval(() => router.refresh(), 5000);
        return () => clearInterval(timer);
    }, [pending, router]);
    const openGroup = (group: Row, sourceId?: string) => router.push(String(group.href) + (sourceId ? '?steps=' + encodeURIComponent(sourceId) : ''));
    return <>
        <header className="page-header"><div><p className="eyebrow"><Link href="/tasks">Task activity</Link> / {selected && <><Link href={'/tasks/' + encodeURIComponent(id)}>{String(d.task.title)}</Link> / Subtask</>}</p><h1 className="task-title">{String(selected?.title || d.task.title)}</h1><p className="page-description">{selected ? <><SemanticBadge value={selected.category} kind="activity"/> <SemanticBadge value={selected.state}/> <SemanticBadge value={selected.outcome}/> · {d.events.length} source steps</> : <>{d.turns.length} native prompts · recorded status <SemanticBadge value={d.task.status}/> · {d.complete ? 'Explained' : 'Unclassified'} · {d.groups.length} subtasks</>}</p></div>{!selected && <div className="page-actions"><MutationDialog action="task-status" title="Record outcome" description="Record explicit acceptance independently of Luna's interpretation." values={{ id }} fields={[{ key: 'status', label: 'Task status', value: ['active', 'waiting', 'completed'].includes(String(d.task.status)) ? d.task.status : 'active', options: ['active', 'waiting', 'completed'].map(value => ({ value, label: value })) }, { key: 'outcome', label: 'Acceptance evidence', type: 'textarea', value: d.task.outcome || '' }]}><Button size="sm" variant="outline">Record outcome</Button></MutationDialog><MutationDialog action="evidence" title="Record evidence" values={{ task_id: id }} fields={[{ key: 'kind', label: 'Evidence kind', options: ['change', 'validation', 'visual_reference', 'intervention'].map(value => ({ value, label: value })) }, { key: 'title', label: 'Title', required: true }, { key: 'detail', label: 'Evidence', type: 'textarea' }, { key: 'outcome', label: 'Outcome', options: ['unknown', 'passed', 'failed', 'confirmed', 'not_applicable'].map(value => ({ value, label: value })) }, { key: 'reference', label: 'Source URL' }]}><Button size="sm" variant="outline">Record evidence</Button></MutationDialog></div>}</header>
        <div className="metric-strip task-metrics">{[['Est. API cost', d.metrics.cost, 'money'], ['Elapsed span', d.duration, 'duration'], ['API calls', d.metrics.responses], ['Tool calls', d.metrics.tools], ['Tokens', d.metrics.tokens, 'tokens'], ['Tool errors', d.metrics.errors]].map(([label, value, type]) => <div className="metric" key={String(label)}><span>{label}</span><strong>{format(value, type as 'money')}</strong></div>)}</div>
        {!selected && <AnalysisCard title="Subtasks" description="Luna breaks the retained task into typed activities. Open a subtask to see only its steps, tools and evidence.">
            <MutationDialog action="analyze" title="Analyze with Luna" description="Queue one analysis through this source's authenticated Codex subscription. No API-key billing, other models or automatic retries." values={{ task_id: id }}><Button size="sm">Analyze with Luna</Button></MutationDialog>
            {!d.complete && <p className="section-note">{d.groups.length ? 'The retained interpretation is stale. Analyze the current evidence before opening subtasks.' : 'No subtasks have been inferred yet. Run Luna analysis to classify this task.'}</p>}
            <DataTable id="task-subtasks" rows={d.groups.map(g => ({ ...g, href: d.complete ? g.href : null }))} columns={[{ key: 'title', label: 'Subtask', type: 'link' }, { key: 'category', label: 'Type', type: 'badge' }, { key: 'state', label: 'State', type: 'badge' }, { key: 'state_basis', label: 'State evidence', hidden: true }, { key: 'outcome', label: 'Outcome', type: 'badge' }, { key: 'outcome_reason', label: 'Why' }, { key: 'failure_reason', label: 'Failure reason' }, { key: 'steps', label: 'Steps', numeric: true }, { key: 'confidence', label: 'Confidence', type: 'percent' }]}/>
            {d.jobs.length > 0 && <DataTable id="task-analysis-jobs" rows={d.jobs} columns={[{ key: 'status', label: 'Analysis status', type: 'badge' }, { key: 'model', label: 'Model' }, { key: 'error', label: 'Error' }]} compact/>}
        </AnalysisCard>}
        {selected && <AnalysisCard title="Subtask outcome" description="Source-backed interpretation; user acceptance remains separate."><div className="evidence-grid"><section><h3>What happened</h3><p>{String(selected.summary)}</p></section><section><h3>State and result</h3><p className="semantic-values"><SemanticBadge value={selected.state}/><SemanticBadge value={selected.outcome}/></p><p>{String(selected.outcome_reason)}</p>{Boolean(selected.state_basis) && <p className="source-note">{String(selected.state_basis)}</p>}</section><section><h3>Why it was unsuccessful</h3><p>{String(selected.failure_reason || (['failed', 'dead_end'].includes(String(selected.outcome)) ? 'No failure explanation recorded.' : 'No unsuccessful outcome established.'))}</p></section></div></AnalysisCard>}
        {!selected && <>
            <AnalysisCard title="Prompt relationships" description="Luna distinguishes a separate task, continued work, course correction and interruption using retained session context. Missing evidence remains unknown."><DataTable id="task-prompt-relations" rows={d.relations} columns={[{ key: 'prompt', label: 'Your prompt' }, { key: 'relationship', label: 'Relationship', type: 'badge' }, { key: 'reason', label: 'Why' }, { key: 'related_prompt', label: 'Related earlier prompt', type: 'link' }, { key: 'confidence', label: 'Confidence', type: 'percent' }, { key: 'started_at', label: 'Started', type: 'date' }]}/></AnalysisCard>
            <AnalysisCard title="Story" description="What was asked, what changed, how it was checked and what remains open" className="task-story-card"><dl className="task-story"><dt>Asked</dt><dd>{String(d.task.goal || d.task.title)}</dd><dt>Changed</dt><dd>{changes.length ? changes.map(n => String(n.title)).join(' · ') : 'No explicit change evidence recorded.'}</dd><dt>Checked</dt><dd>{checks.length ? checks.map(n => String(n.title) + ' — ' + n.outcome).join(' · ') : 'No check evidence recorded.'}</dd><dt>Acceptance</dt><dd>{String(d.task.outcome || 'Unverified')}</dd><dt>{result.schema_version === 2 ? 'Luna outcome' : 'Retained interpretation'}</dt><dd><SemanticBadge value={result.outcome || 'unknown'}/> · {String(result.outcome_reason || 'Awaiting interpretation')}</dd></dl><p className="eyebrow">Timeline · open a subtask</p><div className="phase-track timed-phases">{d.complete && d.groups.map(g => {
                const values = (g.event_ids as string[]).flatMap(id => byId.has(id) ? [byId.get(id)!] : []);
                if (!values.length)
                    return null;
                const a = Math.min(...values.map(e => e.start)), b = Math.max(...values.map(e => e.end));
                return <button key={g.id} aria-label={'Open subtask ' + g.title} title={String(g.category) + ' · ' + String(g.title)} data-activity={String(g.category)} style={{ left: (a - start) / span * 100 + '%', width: Math.max(.3, (b - a) / span * 100) + '%', background: colorFor(g.category) }} onClick={() => openGroup(g)}/>;
            })}</div><div className="chart-legend">{d.groups.map(g => <button key={g.id} disabled={!d.complete} onClick={() => openGroup(g)}><i style={{ background: colorFor(g.category) }}/>{String(g.category)} · {String(g.title)}</button>)}</div><div className="source-markers">{['Images', 'Git calls'].map(label => <div key={label}><small>{label}</small><div className="marker-track">{(label === 'Images' ? d.images.map(i => byId.get(String(i.event_id))).filter(Boolean) : run.filter(e => e.failed === 0 && /(?:^|&&\s*)git\s+(?:(?:-c|-C)\s+\S+\s+)*(?:commit|push)\b/.test(String(e.command)))).map(e => { const group = d.groups.find(g => (g.event_ids as string[]).includes(e!.id)); return group && d.complete ? <button key={e!.id} aria-label={'Open ' + label + ' source ' + e!.id} title={label + ' · ' + e!.id} style={{ left: (e!.end - start) / span * 100 + '%' }} onClick={() => openGroup(group, e!.id)}>{label === 'Images' ? '│' : '◆'}</button> : null; })}</div></div>)}</div></AnalysisCard>
        </>}
        <AnalysisCard title="Evidence" description={selected ? 'Checks and retained images belonging to this subtask' : 'Recorded task evidence'}><div className="evidence-grid"><section><h3>Checks</h3>{checks.length ? checks.map(n => <p key={n.id}>{String(n.title)} · <SemanticBadge value={n.outcome}/><br />{String(n.detail)}</p>) : <p>No test, build or lint evidence recorded.</p>}</section><section><h3>Screenshots</h3><div className="screenshot-grid">{d.images.map(i => <button key={i.id} onClick={() => setImage(i)}><img src={'/api/images/' + encodeURIComponent(i.id)} alt={'Retained screenshot for ' + i.event_id} loading="lazy"/><small>{String(i.event_id)}</small></button>)}</div>{!d.images.length && <p>No retained raster screenshots.</p>}</section><section><h3>Interpretation</h3><p>{String(selected?.summary || d.analysis?.summary || 'No analysis recorded.')}</p><p className="section-note">Model interpretation is separate from acceptance evidence.</p></section></div></AnalysisCard>
        {selected && <>
            <AnalysisCard title="Prompt" defaultOpen={false}><DataTable id="task-prompts" rows={d.turns.map(t => ({ ...t, id: String(t.turn_key) }))} columns={[{ key: 'prompt', label: 'Prompt' }, { key: 'started_at', label: 'Started', type: 'date' }]}/></AnalysisCard>
            <div className="dashboard-grid task-runtime-grid"><AnalysisCard title="Step timeline" description="Only this subtask's finite operations; unknown durations remain points."><div className="native-timeline">{run.slice(0, 300).map(e => <button key={e.id} data-activity={String(e.category)} data-failed={e.failed === 1} title={String(e.category) + ' · ' + String(e.name) + ' · ' + format(e.runtime, 'duration') + (e.failed === 1 ? ' · Tool error' : '')} onClick={() => setIds(e.id)}><span>{e.failed === 1 && <b className="timeline-error" aria-label="Tool error">! </b>}{String(e.model || e.name)}</span><div><i style={{ left: Math.min(99.7, (e.start - start) / span * 100) + '%', width: Math.max(.3, Number(e.runtime || 0) * 1000 / span * 100) + '%', background: colorFor(e.category) }}/></div><small>{format(e.runtime, 'duration')}</small></button>)}</div></AnalysisCard><AnalysisCard title="Tools"><DataTable id="task-tools" kind="tools" extra={scope}/></AnalysisCard></div>
            <AnalysisCard title="Steps" className="span-full">{ids && <Button variant="outline" size="sm" onClick={() => setIds('')}>Clear step filter</Button>}<DataTable id="task-steps" kind="steps" extra={{ ...scope, ...(ids ? { ids } : {}) }}/></AnalysisCard>
        </>}
        <Dialog open={Boolean(image)} onOpenChange={open => !open && setImage(null)}><DialogContent className="evidence-dialog"><DialogHeader><DialogTitle>Retained screenshot</DialogTitle><DialogDescription>{String(image?.event_id || '')}</DialogDescription></DialogHeader>{image && <img className="image-preview" src={'/api/images/' + encodeURIComponent(image.id)} alt="Retained subtask evidence"/>}</DialogContent></Dialog>
    </>;
}
