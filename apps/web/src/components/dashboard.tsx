'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { RefreshCw, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { AnalysisCard } from './analysis-card';
import { DataTable } from './data-table';
import { AnalyticsChart } from './analytics-chart';
import { ScopeControls } from './scope-controls';
import { MutationDialog, type FormField } from './mutation-dialog';
import { PricingEditor } from './pricing-editor';
import { format } from '@/lib/format';
import type { PageData, Scope, Row, Column } from '@/lib/types';
const modes = ['log', 'warn', 'ask', 'block'].map(value => ({ value, label: { log: 'Log only', warn: 'Warn', ask: 'Ask you', block: 'Block' }[value]! }));
export function Dashboard({ view, data, scope }: {
    view: string;
    data: PageData;
    scope: Scope;
}) {
    const router = useRouter(), params = useSearchParams(), path = usePathname(), [selected, setSelected] = useState<Row | null>(null), [turns, setTurns] = useState<Set<string>>(new Set()), [tasks, setTasks] = useState<Set<string>>(new Set());
    const extra = Object.fromEntries(['family', 'action', 'model', 'category', 'day'].flatMap(key => params.get(key) ? [[key, params.get(key)!]] : []));
    const pick = (row: Row) => {
        if (row.chart_id === 'tool-treemap') {
            const query = new URLSearchParams(params);
            query.set('family', String(row.family || 'Shell'));
            if (row.action)
                query.set('action', String(row.action));
            router.push('/tools?' + query);
        }
        else if (Array.isArray(row.task_ids) || Array.isArray(row.event_ids))
            setSelected(row);
        else if (row.href)
            router.push(String(row.href));
        else
            setSelected(row);
    };
    const actionFields = (action: string): FormField[] => action === 'project' ? [{ key: 'name', label: 'Project name', required: true }, { key: 'repo', label: 'Repository path', required: true }, { key: 'scope', label: 'Scope', type: 'textarea' }] : action === 'source-root' ? [{ key: 'path', label: 'Absolute source folder', required: true }, { key: 'provider', label: 'Transcript format', options: [{ value: 'codex', label: 'Codex native JSONL' }, { value: 'claude', label: 'Claude Code JSONL' }] }] : action === 'rule' ? [{ key: 'name', label: 'Rule name', required: true }, { key: 'kind', label: 'Trigger', value: 'command', options: ['command', 'break', 'task_budget', 'daily_budget', 'context', 'failure_loop', 'stop_check'].map(value => ({ value, label: value.replaceAll('_', ' ') })) }, { key: 'mode', label: 'Mode', value: 'warn', options: modes }, { key: 'config', label: 'Trigger configuration', type: 'json', value: { tool: 'Bash', pattern: 'cat ' } }, { key: 'message', label: 'Message to the agent', type: 'textarea', required: true }] : action === 'change' ? [{ key: 'title', label: 'What did you change?', required: true }, { key: 'applied_at', label: 'Applied at', type: 'datetime-local', value: new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16), required: true }, { key: 'takes_effect', label: 'Takes effect', value: 'immediate', options: [{ value: 'immediate', label: 'Immediately' }, { value: 'new_sessions', label: 'Only new sessions' }] }, { key: 'metrics', label: 'Metrics to watch', type: 'json', value: ['cost_per_task', 'context', 'large_context'] }, { key: 'notes', label: 'Notes and evidence', type: 'textarea' }] : action === 'categorization' ? [{ key: 'name', label: 'Rule name', required: true }, { key: 'pattern', label: 'Literal operation pattern', required: true }, { key: 'category', label: 'Category', required: true }, { key: 'activity_type', label: 'Activity type', options: ['productive', 'overhead', 'waiting', 'uncategorized'].map(value => ({ value, label: value })) }, { key: 'priority', label: 'Rule order', type: 'number', value: 100 }] : action === 'task' ? [{ key: 'title', label: 'Task title', required: true }, { key: 'goal', label: 'What should be done?', type: 'textarea', required: true }, { key: 'acceptance', label: 'Acceptance criteria', type: 'textarea' }, { key: 'project_id', label: 'Project', options: data.projects.map(p => ({ value: p.id, label: p.name })) }] : [];
    const actionTitle: Record<string, string> = { project: 'Add project', 'source-root': 'Add source folder', rule: 'Add rule', change: 'Record a change', categorization: 'Add categorization rule', task: 'Define a task', 'analysis-batch': 'Analyze selected scope' };
    return <><header className="page-header"><div><p className="eyebrow">{data.section}</p><h1>{data.title}</h1><p className="page-description">{data.description}</p></div><div className="page-actions">{data.actions?.filter(a => a !== 'assign').map(action => <MutationDialog key={action} action={action} title={actionTitle[action]} description={action === 'analysis-batch' ? 'Freeze the eligible tasks in this scope and queue explicit small-model analysis. Completed or uncertain attempts are not replayed. Analysis overhead is recorded separately.' : undefined} fields={actionFields(action)} values={{ project: scope.project, workspace: scope.workspace, range: scope.range }}><Button size="sm" variant={action === 'analysis-batch' ? 'outline' : 'default'}><Plus size={13}/>{actionTitle[action]}</Button></MutationDialog>)}<Button variant="ghost" size="sm" onClick={() => router.refresh()} aria-label="Refresh page"><RefreshCw size={14}/></Button></div></header>
 <ScopeControls scope={scope} projects={data.projects} workspaces={data.workspaces}/>
 {data.metrics.length > 0 && <div className="metric-strip" style={{ '--metric-count': data.metrics.length } as React.CSSProperties}>{data.metrics.map(metric => { const content = <><span>{metric.label}</span><strong>{format(metric.value, metric.format)}</strong>{metric.note && <small>{metric.note}</small>}</>; return <div className="metric" key={metric.label}>{metric.href ? <Link href={metric.href + '?' + params}>{content}</Link> : content}</div>; })}</div>}
 {view === 'tools' && <div className="tool-controls"><div className="breadcrumbs"><Link href={'/tools?range=' + scope.range}>All tools</Link>{params.get('family') && <> / {params.get('family')}</>}{params.get('action') && <> / <span className="filter-chip">Action is {params.get('action')} <button aria-label="Clear action" onClick={() => { const q = new URLSearchParams(params); q.delete('action'); router.push(path + '?' + q); }}>×</button></span></>}</div><div className="segmented" role="group" aria-label="Treemap measure">{[['calls', 'Calls'], ['runtime', 'Time'], ['call_cost', 'Call cost'], ['context_cost', 'Context cost']].map(([value, label]) => <Button size="sm" variant="ghost" key={value} aria-pressed={(params.get('measure') || 'calls') === value} onClick={() => { const q = new URLSearchParams(params); q.set('measure', value); router.push(path + '?' + q); }}>{label}</Button>)}</div></div>}
 <div className={'dashboard-grid view-' + view}>{data.panels.map(panel => {
            if (panel.id === 'coverage')
                return <AnalysisCard key={panel.id} title={panel.title} className="span-full" description="Semantic charts use only tasks whose current interpreted groups cover their recorded events. Browsing never starts analysis."><div className="coverage-number"><strong>{data.coverage?.complete || 0}</strong> of {data.coverage?.total || 0} tasks</div><div className="coverage-track"><span style={{ width: (data.coverage?.total ? (data.coverage.complete / data.coverage.total) * 100 : 0) + '%' }}/></div><p className="section-note">Explained {data.coverage?.complete || 0} · Unclassified {data.coverage?.unclassified || 0} · Source absence does not establish deletion.</p></AnalysisCard>;
            if (panel.id === 'pricing')
                return <AnalysisCard key={panel.id} title={panel.title} className="span-full"><PricingEditor /></AnalysisCard>;
            const widthClass = panel.list && !(view === 'tools' && panel.id === 'targets') && !['overview', 'fix-workspaces', 'fix-categories'].includes(view) && !['fix-workspaces', 'fix-categories'].includes(panel.id) ? 'span-full' : panel.id === 'flow' || panel.id === 'turns' || panel.id === 'heatmap' ? 'span-full' : '';
            const grouped = view === 'grouping' && ['tasks', 'marked'].includes(panel.id);
            return <AnalysisCard key={panel.id} title={panel.title} description={panel.description || panel.chart?.description} className={widthClass}>
   {panel.chart ? <AnalyticsChart chart={panel.chart} onPick={pick}/> : panel.list ? <DataTable key={panel.list} id={view + '-' + panel.id} kind={panel.list} extra={{ ...extra, ...(view === 'overview' ? { top: '7' } : {}) }} selection={grouped ? (panel.id === 'tasks' ? turns : tasks) : undefined} onSelection={grouped ? (panel.id === 'tasks' ? setTurns : ids => setTasks(new Set([...ids].slice(-1)))) : undefined}/> : panel.text ? <p>{panel.text}</p> : null}
   {view === 'grouping' && panel.id === 'tasks' && <div className="assignment-actions"><MutationDialog action="assign" title="Assign selected native turns" description={`Assign ${turns.size} selected turns to the selected marked task. Existing assignments to a different task require explicit reconciliation.`} values={{ task_id: [...tasks][0], turn_keys: [...turns] }} onSaved={() => { setTurns(new Set()); setTasks(new Set()); }}><Button disabled={!turns.size || tasks.size !== 1}>Assign {turns.size} turns to selected task</Button></MutationDialog></div>}
  </AnalysisCard>;
        })}</div><p className="page-footnote">Native usage is counted once. API-equivalent estimates are not subscription cash charges. Unknown evidence remains unknown.</p>
 <Dialog open={Boolean(selected)} onOpenChange={open => {
            if (!open)
                setSelected(null);
        }}><DialogContent className="evidence-dialog"><DialogHeader><DialogTitle>{String(selected?.name || selected?.date || selected?.title || 'Related evidence')}</DialogTitle><DialogDescription>Inspect the source records behind this chart.</DialogDescription></DialogHeader>{selected && <DataTable id={view + '-chart-drilldown'} kind={Array.isArray(selected.task_ids) ? 'marked' : Array.isArray(selected.event_ids) ? 'steps' : 'tasks'} extra={Array.isArray(selected.task_ids) ? { task_ids: selected.task_ids.join(',') } : Array.isArray(selected.event_ids) ? { ids: selected.event_ids.join(',') } : selected.date ? { day: String(selected.date), ...(selected.series && view === 'tools' ? { tool: String(selected.series) } : {}) } : {}}/>}</DialogContent></Dialog></>;
}
