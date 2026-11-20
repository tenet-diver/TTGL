'use client';
import { useId } from 'react';
import { usePathname } from 'next/navigation';
import { useLocalPreference } from './use-local-preference';
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, Treemap, Cell } from 'recharts';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { DataTable } from './data-table';
import { format } from '@/lib/format';
import { palette, type ChartSpec, type Row } from '@/lib/types';
import { colorFor } from '@/lib/semantic-colors';
export function AnalyticsChart({ chart, onPick }: {
    chart: ChartSpec;
    onPick: (row: Row) => void;
}) {
    const path = usePathname(), key = 'observatory-chart:' + path + ':' + chart.id;
    const [daily, setDaily] = useLocalPreference(key + ':daily', true, value => typeof value === 'boolean' ? value : true);
    const [average, setAverage] = useLocalPreference(key + ':average', true, value => typeof value === 'boolean' ? value : true);
    const [showValues, setShowValues] = useLocalPreference(key + ':source-values', false, value => typeof value === 'boolean' ? value : false);
    const data = chart.points;
    if (!data.some(p => chart.series.some(s => typeof p[s.key] === 'number')) && !['flow', 'turns', 'heatmap'].includes(chart.kind))
        return <p className="empty-chart">No supported observations in this scope. Missing source counters stay unknown.</p>;
    const pick = (row: Record<string, unknown>) => onPick({ ...row, id: String(row.id || row.date || row.name || chart.id), chart_id: chart.id });
    if (chart.id === 'overview-model-cost') {
        const max = Math.max(...data.map(row => Number(row.value) || 0), .001);
        return <div className="overview-ranking" role="group" aria-label={chart.title}>
            {data.map(row => {
                const color = colorFor(row.name, 'model');
                return <button type="button" key={String(row.name)} onClick={() => pick(row)}>
                    <span><i style={{ background: color }}/>{String(row.name)} <strong>{format(row.value, 'money')}</strong></span>
                    <span className="bar-track"><span style={{ width: Number(row.value) / max * 100 + '%', background: color }}/></span>
                </button>;
            })}
        </div>;
    }
    if (chart.kind === 'horizontal') {
        const max = Math.max(1, ...data.map(p => Number(p.value) || 0));
        return <div className="category-bars">{data.map(row => <button key={String(row.name)} onClick={() => pick(row)}><span><i style={{ background: colorFor(row.name, chart.colorKind) }}/>{String(row.name)}</span><span className="bar-track"><span style={{ width: row.value == null ? '0' : Math.max(1, Number(row.value) / max * 100) + '%', background: colorFor(row.name, chart.colorKind) }}/></span><strong>{format(row.value, chart.id.includes('cost') ? 'money' : chart.id.includes('time') || chart.id === 'activity' ? 'duration' : undefined)}</strong></button>)}</div>;
    }
    if (chart.kind === 'heatmap')
        return <Heatmap chart={chart} onPick={pick}/>;
    if (chart.kind === 'turns')
        return <TurnTracks chart={chart} onPick={pick}/>;
    if (chart.kind === 'flow')
        return <ProcessFlow chart={chart} onPick={pick}/>;
    if (chart.kind === 'treemap') {
        const points = data.filter(p => Number(p.value) > 0).map(p => ({ ...p, color: colorFor(p.name, chart.colorKind) }));
        return <div className="chart-treemap" role="group" aria-label={chart.title}><ResponsiveContainer width="100%" height={350}><Treemap data={points} dataKey="value" aspectRatio={1.4} isAnimationActive={false} content={<TreemapCell onPick={pick}/>}><Tooltip formatter={value => format(value)}/></Treemap></ResponsiveContainer></div>;
    }
    const axisStyle = { fontSize: 10, fill: 'var(--muted-foreground)' };
    return <><div className="chart-viewport" role="group" aria-label={chart.title}><ResponsiveContainer width="100%" height={chart.id === 'overview-turns' ? 212 : 230}>{chart.kind === 'line' ? <LineChart data={data} margin={{ left: 0, right: 12, top: 10, bottom: 5 }}><CartesianGrid vertical={false} stroke="var(--border)"/><XAxis dataKey="date" tick={axisStyle} tickFormatter={v => String(v).slice(5)} minTickGap={35}/><YAxis tick={axisStyle} width={54} tickFormatter={v => format(v, chart.id.includes('context') ? 'tokens' : undefined)}/><Tooltip contentStyle={{ background: 'var(--card)', borderColor: 'var(--border)', fontSize: 12 }}/>{daily && <Line dataKey="value" name="Per day" stroke="transparent" dot={{ r: 2, fill: chart.series[0]?.color || 'var(--tone-neutral)' }} activeDot={{ r: 4 }} connectNulls={false} isAnimationActive={false}/>} {average && <Line dataKey="average" name="7-day average" stroke={chart.series[1]?.color || palette[0]} strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false}/>} {chart.markers?.map(marker => <ReferenceLine key={marker.number} x={marker.at.slice(0, 10)} stroke="var(--muted-foreground)" strokeDasharray="3 3" label={{ value: marker.number, position: 'top', fontSize: 10, fill: 'var(--foreground)' }}/>)}</LineChart> : <BarChart data={data} margin={{ left: 0, right: 12, top: 10, bottom: 5 }}><CartesianGrid vertical={false} stroke="var(--border)"/><XAxis dataKey="date" tick={axisStyle} tickFormatter={v => String(v).includes('T') ? String(v).slice(5, 10) : String(v).length === 10 ? String(v).slice(5) : String(v)} minTickGap={24}/><YAxis tick={axisStyle} width={54} tickFormatter={v => format(v, chart.id.includes('token') ? 'tokens' : undefined)}/><Tooltip contentStyle={{ background: 'var(--card)', borderColor: 'var(--border)', fontSize: 12 }}/><Legend wrapperStyle={{ fontSize: 10 }}/>{chart.series.map(s => <Bar key={s.key} dataKey={s.key} name={s.name} fill={s.color} stackId="native" isAnimationActive={false} onClick={(data) => {
                    const point = data as unknown as {
                        payload: Record<string, unknown>;
                    };
                    if (point.payload)
                        pick({ ...point.payload, series: s.key });
                }} style={{ cursor: 'pointer' }}/>)}</BarChart>}</ResponsiveContainer></div>{chart.kind === 'line' && <div className="chart-legend"><label><Checkbox checked={daily} onCheckedChange={v => setDaily(Boolean(v))}/><i style={{ background: chart.series[0]?.color }}/>Per day</label><label><Checkbox checked={average} onCheckedChange={v => setAverage(Boolean(v))}/><i style={{ background: chart.series[1]?.color }}/>7-day average</label><span>Last 7 days <strong>{format(chart.last)}</strong></span></div>}<details className="chart-values" open={showValues} onToggle={e => setShowValues(e.currentTarget.open)}><summary>Source values</summary>{showValues && <DataTable id={'chart-' + chart.id} rows={data.map((r, i) => ({ ...r, id: String(r.date || i) }))} columns={[{ key: 'date', label: 'Date' }, ...chart.series.map(s => ({ key: s.key, label: s.name, numeric: true }))]} compact/>}</details></>;
}
function TreemapCell(props: Record<string, unknown> & {
    onPick: (row: Record<string, unknown>) => void;
}) {
    const { x, y, width, height, name, color, onPick, ...rest } = props;
    const w = Number(width) || 0, h = Number(height) || 0;
    if (!name || w < 2 || h < 2)
        return <g />;
    const title = String(name), pick = () => onPick({ name: title, ...rest });
    return <g transform={`translate(${Number(x) || 0},${Number(y) || 0})`} role="button" tabIndex={0} aria-label={title} onClick={pick} onKeyDown={e => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                pick();
            }
        }} style={{ cursor: 'pointer' }}><title>{title + ': ' + format(rest.value)}</title><rect width={w} height={h} fill={String(color || palette[0])} stroke="var(--card)" strokeWidth={1} rx={2}/>{w > 55 && h > 30 && <text x={6} y={17} fill="#111" fontSize={11}><tspan>{title.length > w / 6 ? title.slice(0, Math.max(5, Math.floor(w / 6) - 2)) + '…' : title}</tspan>{h > 45 && <tspan x={6} dy={15}>{format(rest.value)}</tspan>}</text>}</g>;
}
function Heatmap({ chart, onPick }: {
    chart: ChartSpec;
    onPick: (r: Record<string, unknown>) => void;
}) { const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], max = Math.max(1, ...chart.points.map(p => Number(p.value) || 0)); return <div className="horizontal-scroll"><div className="heatmap"><span />{Array.from({ length: 24 }, (_, i) => <small key={i}>{i % 3 === 0 ? i : ''}</small>)}{days.map(day => <div className="heatmap-row" key={day}><span>{day}</span>{Array.from({ length: 24 }, (_, hour) => { const row = chart.points.find(p => p.day === day && p.hour === hour); return <button key={hour} disabled={!row} aria-label={`${day} ${hour}:00 ${row ? format(row.value, 'money') : 'No observations'}`} style={{ background: row && row.known ? `color-mix(in srgb, ${palette[0]} ${Math.max(20, Number(row.value) / max * 100)}%,var(--muted))` : undefined }} onClick={() => row && onPick(row)}/>; })}</div>)}</div><p className="section-note">Less <span className="heat-gradient"/> More · Native API-equivalent cost; empty cells mean no retained observations.</p></div>; }
function TurnTracks({ chart, onPick }: {
    chart: ChartSpec;
    onPick: (r: Record<string, unknown>) => void;
}) {
    const groups = new Map<string, Record<string, unknown>[]>();
    for (const point of chart.points) {
        if (!point.started)
            continue;
        const date = String(point.display_date || point.started).slice(0, 10);
        if (!groups.has(date))
            groups.set(date, []);
        groups.get(date)!.push(point);
    }
    const modelNames = [...new Set(chart.points.map(p => String(p.models || 'Unknown')))];
    return <><div className="chart-legend" aria-label="Model colours">{modelNames.map(name => <label key={name}><i style={{ background: colorFor(name, 'model') }}/>{name}</label>)}</div><div className="horizontal-scroll"><div className="turn-tracks"><div className="day-ruler"><span />{[0, 3, 6, 9, 12, 15, 18, 21, 24].map(h => <small key={h} style={{ left: `calc(100px + (100% - 100px) * ${h / 24})` }}>{h}:00</small>)}</div>{[...groups].sort(([a], [b]) => b.localeCompare(a)).slice(0, 120).map(([date, turns]) => <div className="turn-day" key={date}><span>{date}</span><div>{turns.map((turn, i) => { const hour = Number(turn.start_hour) || 0; return <button key={String(turn.id) + i} style={{ left: hour / 24 * 100 + '%', width: Math.max(.25, Number(turn.span_hours || 0) / 24 * 100) + '%', top: (i % 2) * 4, background: colorFor(turn.models || 'Unknown', 'model') }} aria-label={String(turn.title)} title={String(turn.title) + ' · ' + String(turn.models || 'Unknown model') + ' · ' + format(turn.duration, 'duration')} onClick={() => onPick(turn)}/>; })}</div></div>)}</div></div></>;
}
function ProcessFlow({ chart, onPick }: {
    chart: ChartSpec;
    onPick: (r: Record<string, unknown>) => void;
}) {
    const marker = useId().replaceAll(':', ''), path = usePathname(), nodes = chart.points.filter(p => p.kind === 'node'), edges = chart.points.filter(p => p.kind === 'edge');
    const [requestedCount, setCount] = useLocalPreference('observatory-chart:' + path + ':' + chart.id + ':connections', 24, value => typeof value === 'number' && Number.isInteger(value) && value >= 1 && value <= 1000 ? value : 24);
    const count = Math.min(requestedCount, edges.length);
    const names = ['Start', ...nodes.map(n => String(n.name)), 'End'], max = Math.max(1, ...edges.map(e => Number(e.times))), height = names.length * 78 + 20, total = edges.reduce((s, e) => s + Number(e.times), 0), shown = edges.slice(0, count).reduce((s, e) => s + Number(e.times), 0);
    return <><label className="flow-limit">Connections<Input type="range" aria-label="Connections" min={1} max={Math.max(1, edges.length)} value={count} onChange={e => setCount(Number(e.target.value))}/><span>{count} of {edges.length} · {format(total ? shown / total : 0, 'percent')} of all moves</span></label><div className="horizontal-scroll"><svg className="process-map" viewBox={`0 0 720 ${height}`} role="group" aria-label="Task process map"><defs><marker id={marker} markerWidth="4" markerHeight="4" refX="7" refY="4" viewBox="0 0 8 8" orient="auto"><path d="M0 0 L8 4 L0 8Z" fill="context-stroke"/></marker></defs>{edges.slice(0, count).map((edge, i) => {
            const a = names.indexOf(String(edge.from)), b = names.indexOf(String(edge.to)), back = Number(edge.rework) > 0, side = back ? 270 : 450, y1 = a * 78 + 35, y2 = b * 78 + 35, adjacent = b === a + 1 && !back, arc = back ? Math.max(40, 240 - Math.abs(a - b) * 20) : Math.min(690, 480 + Math.abs(a - b) * 25), path = adjacent ? `M360 ${y1 + 22} L360 ${y2 - 22}` : a === b ? `M${side} ${y1 - 8} C${arc} ${y1 - 50} ${arc} ${y1 + 50} ${side} ${y1 + 8}` : `M${side} ${y1} C${arc} ${y1} ${arc} ${y2} ${side} ${y2}`;
            return <g key={i}><path d={path} fill="none" stroke={back ? 'var(--tone-warning)' : colorFor(edge.from === 'Start' ? edge.to : edge.from)} strokeWidth={1 + Math.sqrt(Number(edge.times) / max) * 3} strokeDasharray={back ? '4 3' : undefined} markerEnd={`url(#${marker})`} tabIndex={0} role="button" aria-label={`${edge.from} to ${edge.to}: ${edge.times} transitions`} onClick={() => onPick(edge)} onKeyDown={e => {
                    if (e.key === 'Enter')
                        onPick(edge);
                }}><title>{`${edge.from} → ${edge.to} · ${edge.times} moves`}</title></path><text x={adjacent ? 370 : side + (arc - side) * .7} y={(y1 + y2) / 2 - 4} className="flow-count">{String(edge.times)}</text></g>;
        })}{names.map((name, i) => {
            const node = nodes.find(n => n.name === name), y = i * 78 + 12;
            return <g key={name} role="button" tabIndex={0} aria-label={name + ': show tasks'} onClick={() => node && onPick(node)} onKeyDown={e => {
                    if (e.key === 'Enter' && node)
                        onPick(node);
                }}><rect x={node ? 270 : 325} y={y} width={node ? 180 : 70} height={node ? 58 : 28} rx={node ? 6 : 14} fill={node ? `color-mix(in srgb, ${colorFor(name)} 10%, var(--card))` : 'var(--card)'} stroke={node ? colorFor(name) : 'var(--border)'}/>{node && <circle cx={281} cy={y + 15} r={4} fill={colorFor(name)}/>}<text x={node ? 291 : 344} y={y + 19} fill="var(--foreground)" fontSize={12}>{name}</text>{node && <text x={280} y={y + 35} fill="var(--muted-foreground)" fontSize={9}>{format(node.subtasks)} subtasks · {format(node.tasks)} tasks · {format(node.cost, 'money')}</text>}{node && <text x={280} y={y + 48} fill="var(--muted-foreground)" fontSize={9}>{`${node.completed || 0} completed · ${node.blocked || 0} blocked · ${node.failed || 0} unsuccessful`}</text>}</g>;
        })}</svg></div><p className="section-note">Solid paths move forward; dashed paths return to a category already visited. Paths are interpretations.</p></>;
}
