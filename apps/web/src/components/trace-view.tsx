import Link from 'next/link';
import { ChevronLeft } from 'lucide-react';
import { DataTable } from './data-table';
import { AnalysisCard } from './analysis-card';
import { format } from '@/lib/format';
import { context, metrics } from '@/lib/repository';
import { pg } from '@/lib/database';

export async function TraceView({ turn, tab, query }: { turn: string; tab: string; query: URLSearchParams }) {
    const [identity] = await pg()`SELECT session_id FROM turns WHERE turn_key=${turn}`;
    if (!identity) return <section className="trace-content"><h1>Trace unavailable</h1><Link href="/turns">Back to turns</Link></section>;
    const session = String(identity.session_id);
    const ctx = await context({ workspace: '', project: '', range: 'all', timezone: 'UTC', session });
    const record = ctx.turns.find(item => item.turn_key === turn);
    if (!record) return <section className="trace-content"><h1>Trace unavailable</h1><Link href="/turns">Back to turns</Link></section>;
    const events = ctx.events.filter(event => event.turn_key === turn);
    const m = metrics(events, ctx.pricing);
    const selected = ['summary', 'waterfall', 'conversation'].includes(tab) ? tab : 'summary';
    const returnQuery = new URLSearchParams(query);
    returnQuery.delete('turn'); returnQuery.delete('tab');
    const to = (view: string) => '/trace?' + new URLSearchParams({ ...Object.fromEntries(query), turn, tab: view });
    const response = record.source.last_message;
    const value = typeof response === 'string' ? response : response ? JSON.stringify(response, null, 2) : '';
    const task = ctx.assignments.get(turn);
    const spans = events.filter(e => e.time_known && e.runtime != null && e.runtime_role !== 'background_service_lifetime').map(e => ({ id: e.id, label: e.kind === 'generation' ? e.model || 'Model response' : e.name, start: Date.parse(e.event_time) / 1000 - Number(e.runtime), duration: Number(e.runtime) }));
    const beginning = spans.length ? Math.min(...spans.map(span => span.start)) : 0;
    const total = spans.length ? Math.max(...spans.map(span => span.start + span.duration)) - beginning : 0;

    return <section className="trace-content dashboard-content">
        <Link className="trace-back" href={'/turns?' + returnQuery}><ChevronLeft size={15}/> Back to turns</Link>
        <header className="page-header"><div><p className="eyebrow">Work / Turns</p><h1>Trace inspector</h1><p className="page-description">{record.prompt.split('\n')[0].slice(0, 210) || 'No retained prompt'}</p></div>{task && <Link href={'/tasks/' + encodeURIComponent(task)}>Open work item</Link>}</header>
        <nav className="dashboard-tabs" aria-label="Trace views">{['summary', 'waterfall', 'conversation'].map(view => <Link key={view} href={to(view)} aria-current={selected === view ? 'page' : undefined}>{view[0].toUpperCase() + view.slice(1)}</Link>)}</nav>
        <div className="trace-panels">
            {selected === 'summary' && <>
                <div className="metric-strip" style={{ '--metric-count': 4 } as React.CSSProperties}>
                    {[['Estimated cost', format(m.cost, 'money')], ['Tokens', format(m.tokens, 'tokens')], ['Tool calls', format(m.tools)], ['Failed calls', format(m.errors)]].map(([label, number]) => <div className="metric" key={label}><span>{label}</span><strong>{number}</strong></div>)}
                </div>
                <AnalysisCard title="Native evidence" description={`${record.harness || 'Unknown'} · ${format(record.started_at, 'date')}`} collapsible={false}>
                    <DataTable id="trace-native-steps" kind="steps" extra={{ range: 'all', workspace: '', project: '', work: '', harness: '', scopeModel: '', day: '', session, native_turn: turn }}/>
                </AnalysisCard>
            </>}
            {selected === 'waterfall' && <AnalysisCard title="Recorded operation timing" description="Operations without native runtime are omitted. Concurrent spans can overlap." collapsible={false}>
                <div className="trace-waterfall">{spans.length ? spans.map(span => <div className="trace-span" key={span.id}>
                    <span title={span.label}>{span.label}</span><span className="bar-track"><span style={{ left: (total ? (span.start - beginning) / total * 100 : 0) + '%', width: (total ? span.duration / total * 100 : 0) + '%' }}/></span><small>{format(span.duration, 'duration')}</small>
                </div>) : <p className="section-note">No recorded operation durations for this turn.</p>}</div>
            </AnalysisCard>}
            {selected === 'conversation' && <>
                <AnalysisCard title="User prompt" collapsible={false}><pre>{record.prompt || 'No retained prompt.'}</pre></AnalysisCard>
                <AnalysisCard title="Last retained response" collapsible={false}><pre>{value || 'No assistant message was retained for this turn.'}</pre></AnalysisCard>
            </>}
        </div>
    </section>;
}
