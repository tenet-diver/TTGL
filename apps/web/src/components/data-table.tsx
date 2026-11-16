'use client';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import { useReactTable, getCoreRowModel, flexRender, type ColumnDef, type VisibilityState } from '@tanstack/react-table';
import { ArrowDown, ArrowUp, ArrowUpDown, Columns3, ChevronLeft, ChevronRight, Search, X, MoreHorizontal } from 'lucide-react';
import { Table, TableHeader, TableHead, TableRow, TableBody, TableCell } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuCheckboxItem } from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectTrigger, SelectContent, SelectValue, SelectItem } from '@/components/ui/select';
import { MutationDialog, mutate, type FormField } from './mutation-dialog';
import { format } from '@/lib/format';
import { collection } from '@/lib/record-query';
import type { Row, Column, RecordPage, Query } from '@/lib/types';
const initial: Query = { search: '', filters: {}, sort: null, direction: 1, offset: 0, limit: 20 };
const modeOptions = ['log', 'warn', 'ask', 'block'].map(value => ({ value, label: { log: 'Log only', warn: 'Warn', ask: 'Ask you', block: 'Block' }[value]! }));
export function DataTable({ id, kind, rows: localRows, columns: localColumns, extra = {}, compact = false, selection, onSelection }: {
    id: string;
    kind?: string;
    rows?: Row[];
    columns?: Column[];
    extra?: Record<string, string>;
    compact?: boolean;
    selection?: Set<string>;
    onSelection?: (ids: Set<string>) => void;
}) {
    const params = useSearchParams(), router = useRouter(), [query, setQuery] = useState<Query>(initial), [visibility, setVisibility] = useState<VisibilityState>({}), [ready, setReady] = useState(false), [filtersOpen, setFiltersOpen] = useState(false), [data, setData] = useState<RecordPage>({ rows: [], total: 0, offset: 0, limit: 20, columns: [] }), [pending, setPending] = useState(true), [error, setError] = useState(''), [revision, setRevision] = useState(0), [detail, setDetail] = useState<Row | null>(null), [source, setSource] = useState<unknown>(null), [sourcePending, setSourcePending] = useState(false);
    const [contextFilter, setContextFilter] = useState<{
        key: string;
        value: unknown;
        label: string;
    } | null>(null);
    useEffect(() => { const reload = () => setRevision(r => r + 1); window.addEventListener('observatory-records-changed', reload); return () => window.removeEventListener('observatory-records-changed', reload); }, []);
    const scope = params.toString(), extraKey = JSON.stringify(extra), queryKey = JSON.stringify(query), localKey = JSON.stringify(localColumns), rowsKey = JSON.stringify(localRows);
    useEffect(() => {
        try {
            const saved = JSON.parse(localStorage.getItem('observatory-table:' + id) || '{}');
            if (saved.query)
                setQuery({ ...initial, ...saved.query });
            if (saved.visibility)
                setVisibility(saved.visibility);
            if (saved.filtersOpen)
                setFiltersOpen(true);
        }
        catch { }
        setReady(true);
    }, [id]);
    useEffect(() => {
        if (ready)
            localStorage.setItem('observatory-table:' + id, JSON.stringify({ query, visibility, filtersOpen }));
    }, [id, ready, queryKey, visibility, filtersOpen]);
    useEffect(() => {
        if (!ready)
            return;
        const controller = new AbortController();
        const timer = setTimeout(async () => {
            setPending(true);
            setError('');
            try {
                let result: RecordPage;
                if (localRows && localColumns)
                    result = { ...collection(localRows, query, localColumns.map(c => c.key)), columns: localColumns };
                else {
                    const search = new URLSearchParams(scope);
                    Object.entries(JSON.parse(extraKey) as Record<string, string>).forEach(([k, v]) => search.set(k, v));
                    search.set('query', queryKey);
                    const response = await fetch('/api/records/' + kind + '?' + search, { signal: controller.signal });
                    result = await response.json();
                    if (!response.ok)
                        throw Error((result as unknown as {
                            error: string;
                        }).error || 'Records unavailable');
                }
                if (controller.signal.aborted)
                    return;
                setData(result);
                setVisibility(previous => Object.keys(previous).length ? previous : Object.fromEntries(result.columns.filter(c => c.hidden).map(c => [c.key, false])));
                if (result.offset !== query.offset)
                    setQuery(previous => ({ ...previous, offset: result.offset }));
            }
            catch (e) {
                if (!controller.signal.aborted)
                    setError(e instanceof Error ? e.message : 'Records unavailable');
            }
            finally {
                if (!controller.signal.aborted)
                    setPending(false);
            }
        }, query.search || Object.values(query.filters).some(Boolean) ? 180 : 0);
        return () => { clearTimeout(timer); controller.abort(); };
    }, [id, kind, scope, extraKey, queryKey, ready, revision, localKey, rowsKey]);
    const update = (values: Partial<Query>) => setQuery(q => ({ ...q, offset: 0, ...values }));
    const refresh = () => { setRevision(r => r + 1); router.refresh(); };
    const open = async (row: Row) => {
        setDetail(row);
        setSource(null);
        if (row.event_id) {
            setSourcePending(true);
            try {
                const response = await fetch('/api/events/' + encodeURIComponent(String(row.event_id)));
                const body = await response.json();
                if (!response.ok)
                    throw Error(body.error);
                setSource(body);
            }
            catch (e) {
                setSource({ error: e instanceof Error ? e.message : 'Source unavailable' });
            }
            finally {
                setSourcePending(false);
            }
        }
    };
    const cell = (row: Row, column: Column): ReactNode => {
        const value = row[column.key];
        if (column.key === 'archive_id' && value)
            return <a href={'/api/raw/' + encodeURIComponent(String(value))}>Download original</a>;
        if (kind === 'rules' && column.key === 'enabled')
            return <Switch aria-label={'Enable ' + row.name} checked={Boolean(value)} disabled={pending} onCheckedChange={async (enabled) => {
                    try {
                        await mutate('rule', { id: row.id, enabled });
                        refresh();
                    }
                    catch (e) {
                        setError(String(e));
                    }
                }}/>;
        if (kind === 'rules' && column.key === 'mode')
            return <Select value={String(value)} onValueChange={async (mode) => {
                    try {
                        await mutate('rule', { id: row.id, mode });
                        refresh();
                    }
                    catch (e) {
                        setError(String(e));
                    }
                }}><SelectTrigger aria-label={'Mode for ' + row.name} className="mode-select"><SelectValue /></SelectTrigger><SelectContent>{modeOptions.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent></Select>;
        if (kind === 'changes' && column.key === 'title')
            return <div className="change-description"><strong><Badge variant="outline">{String(row.number)}</Badge> {String(value)}</strong><small>{format(row.applied_at, 'date')} · {String(row.takes_effect).replaceAll('_', ' ')}</small><p>{String(row.notes || '')}</p></div>;
        if (column.key === 'comparison' && Array.isArray(value))
            return <DataTable id={id + '-' + row.id} rows={value as Row[]} columns={[{ key: 'metric', label: 'Metric' }, { key: 'before', label: 'Before', numeric: true }, { key: 'after', label: 'After', numeric: true }, { key: 'change', label: 'Change' }]} compact/>;
        if (['before', 'after'].includes(column.key) && row.sample_unit)
            return <div>{format(value, String(row.format))}<small className="sample-note">{format(row[column.key + '_count'])} {String(row.sample_unit)} · {format(row[column.key + '_hours'])} hours</small></div>;
        if (column.key === 'change' && row.sample_unit)
            return <div><Badge variant="outline">{String(value)}</Badge>{row.low != null && <small className="sample-note">95% Δ {format(row.low, String(row.format))} to {format(row.high, String(row.format))}</small>}</div>;
        if (column.type === 'link' && row.href)
            return <Link href={String(row.href)} className="record-link">{format(value)}</Link>;
        if (column.type === 'badge')
            return <Badge variant="outline"><i className={'badge-dot ' + (/fail|fix|error|block/i.test(String(value)) ? 'error' : /warn|ask|pending/i.test(String(value)) ? 'warning' : 'neutral')}/>{format(value)}</Badge>;
        if (column.type === 'code')
            return <code title={String(value ?? '')}>{format(value)}</code>;
        if (typeof value === 'object' && value !== null)
            return <span className="table-prose">{format(value)}</span>;
        return format(value, column.type);
    };
    const definitions = useMemo<ColumnDef<Row>[]>(() => {
        const defs: ColumnDef<Row>[] = data.columns.map(column => ({ id: column.key, accessorFn: row => row[column.key], header: column.label, cell: ctx => cell(ctx.row.original, column), enableSorting: true }));
        if (onSelection)
            defs.unshift({ id: '__selection', header: () => <Checkbox aria-label={'Select this page ' + id} checked={data.rows.length > 0 && data.rows.every(r => selection?.has(r.id))} onCheckedChange={checked => { const next = new Set(selection); data.rows.forEach(r => checked ? next.add(r.id) : next.delete(r.id)); onSelection(next); }}/>, cell: ctx => <Checkbox aria-label={'Select ' + String(ctx.row.original.title || ctx.row.id)} checked={Boolean(selection?.has(ctx.row.original.id))} onCheckedChange={checked => { const next = new Set(selection); checked ? next.add(ctx.row.original.id) : next.delete(ctx.row.original.id); onSelection(next); }}/>, enableSorting: false, enableHiding: false });
        if (kind)
            defs.push({ id: '__actions', header: '', enableSorting: false, enableHiding: false, cell: ctx => <RowActions kind={kind} row={ctx.row.original} onSaved={refresh} onInspect={() => void open(ctx.row.original)}/> });
        return defs;
    }, [data.columns, kind, queryKey, selection, pending]);
    const table = useReactTable({ data: data.rows, columns: definitions, getRowId: row => row.id, getCoreRowModel: getCoreRowModel(), manualPagination: true, manualFiltering: true, manualSorting: true, state: { columnVisibility: visibility }, onColumnVisibilityChange: setVisibility });
    const pages = Math.max(1, Math.ceil(data.total / query.limit)), page = Math.floor(data.offset / query.limit) + 1, active = Boolean(query.search || query.sort || Object.values(query.filters).some(Boolean));
    return <div className={'record-list ' + (compact ? 'compact-list' : '')} data-list={id} aria-busy={pending}>
 <div className="list-toolbar"><span className="record-count">{data.total.toLocaleString()} records{selection?.size ? ` · ${selection.size} selected` : ''}</span><div className="list-controls"><DropdownMenu><DropdownMenuTrigger asChild><Button variant="outline" size="sm" aria-label={'Columns ' + id}><Columns3 size={13}/>Columns {table.getVisibleLeafColumns().filter(c => c.id !== '__actions' && c.id !== '__selection').length}/{data.columns.length}</Button></DropdownMenuTrigger><DropdownMenuContent align="end">{table.getAllColumns().filter(c => c.getCanHide()).map(column => <DropdownMenuCheckboxItem key={column.id} checked={column.getIsVisible()} onSelect={e => e.preventDefault()} onCheckedChange={checked => {
                column.toggleVisibility(Boolean(checked));
                if (!checked) {
                    const filters = { ...query.filters };
                    delete filters[column.id];
                    update({ filters, sort: query.sort === column.id ? null : query.sort });
                }
            }}>{String(column.columnDef.header)}</DropdownMenuCheckboxItem>)}</DropdownMenuContent></DropdownMenu><Button variant="outline" size="sm" aria-expanded={filtersOpen} onClick={() => setFiltersOpen(!filtersOpen)}>Filters</Button>{active && <Button variant="ghost" size="sm" onClick={() => { setQuery(initial); setVisibility(Object.fromEntries(data.columns.filter(c => c.hidden).map(c => [c.key, false]))); setFiltersOpen(false); }}>Reset</Button>}<div className="table-search"><Search size={13}/><Input aria-label={'Search ' + id} placeholder="Search" value={query.search} onChange={e => update({ search: e.target.value })}/>{query.search && <Button variant="ghost" size="icon" aria-label={'Clear search ' + id} onClick={() => update({ search: '' })}><X size={12}/></Button>}</div></div></div>
 {error && <p role="alert" className="error-message">{error}<Button variant="link" onClick={() => setRevision(r => r + 1)}>Retry</Button></p>}
 <Table><TableHeader>{table.getHeaderGroups().map(group => <TableRow key={group.id}>{group.headers.map(header => <TableHead key={header.id} className={data.columns.find(c => c.key === header.id)?.numeric ? 'numeric' : ''}>{header.isPlaceholder ? null : header.column.getCanSort() ? <Button variant="ghost" className="sort-button" aria-label={'Sort by ' + String(header.column.columnDef.header)} onClick={() => update(query.sort === header.id ? query.direction === 1 ? { direction: -1 } : { sort: null, direction: 1 } : { sort: header.id, direction: 1 })} aria-pressed={query.sort === header.id}>{flexRender(header.column.columnDef.header, header.getContext())}{query.sort === header.id ? query.direction === 1 ? <ArrowUp size={11}/> : <ArrowDown size={11}/> : <ArrowUpDown size={11}/>}</Button> : flexRender(header.column.columnDef.header, header.getContext())}</TableHead>)}</TableRow>)}{filtersOpen && <TableRow>{table.getVisibleLeafColumns().map(col => <TableHead key={col.id}>{col.getCanSort() && <Input aria-label={'Filter ' + id + ' by ' + String(col.columnDef.header)} placeholder={data.columns.find(c => c.key === col.id)?.numeric ? 'e.g. >= 100' : 'Filter…'} value={query.filters[col.id] || ''} onChange={e => update({ filters: { ...query.filters, [col.id]: e.target.value } })}/>}</TableHead>)}</TableRow>}</TableHeader><TableBody>{table.getRowModel().rows.length ? table.getRowModel().rows.map(row => <TableRow key={row.id}>{row.getVisibleCells().map(ctx => <TableCell key={ctx.id} onContextMenu={event => {
                    if (ctx.column.id.startsWith('__'))
                        return;
                    event.preventDefault();
                    setContextFilter({ key: ctx.column.id, value: ctx.getValue(), label: String(ctx.column.columnDef.header) });
                }} className={data.columns.find(c => c.key === ctx.column.id)?.numeric ? 'numeric' : ''}>{flexRender(ctx.column.columnDef.cell, ctx.getContext())}</TableCell>)}</TableRow>) : <TableRow><TableCell colSpan={Math.max(1, table.getVisibleLeafColumns().length)} className="table-empty">{pending ? 'Loading records…' : active ? 'No matching records. Clear the filters to see the full scope.' : 'No records in this scope.'}</TableCell></TableRow>}</TableBody></Table>
 {(!compact || data.total > query.limit) && <div className="list-pagination"><span>{data.total ? data.offset + 1 : 0}–{Math.min(data.offset + data.rows.length, data.total)} of {data.total}</span><label>Rows per page<Select value={String(query.limit)} onValueChange={value => update({ limit: Number(value) })}><SelectTrigger aria-label={'Rows per page ' + id}><SelectValue /></SelectTrigger><SelectContent>{[10, 20, 50, 100].map(n => <SelectItem key={n} value={String(n)}>{n}</SelectItem>)}</SelectContent></Select></label><div className="page-buttons"><Button variant="ghost" size="sm" aria-label={'Previous page ' + id} disabled={pending || page <= 1} onClick={() => update({ offset: Math.max(0, data.offset - query.limit) })}><ChevronLeft size={12}/>Previous</Button><label className="page-jump">Page<Input type="number" min="1" max={pages} aria-label={'Page ' + id} value={page} onChange={e => {
                const target = Number(e.target.value);
                if (target >= 1 && target <= pages)
                    update({ offset: (target - 1) * query.limit });
            }}/></label><span>of {pages}</span><Button variant="ghost" size="sm" aria-label={'Next page ' + id} disabled={pending || page >= pages} onClick={() => update({ offset: data.offset + query.limit })}>Next<ChevronRight size={12}/></Button></div></div>}
 <Dialog open={Boolean(contextFilter)} onOpenChange={open => {
            if (!open)
                setContextFilter(null);
        }}><DialogContent><DialogHeader><DialogTitle>Filter exact value</DialogTitle><DialogDescription>{contextFilter?.label}: {format(contextFilter?.value)}</DialogDescription></DialogHeader><Button onClick={() => {
            if (contextFilter) {
                update({ filters: { ...query.filters, [contextFilter.key]: '==' + JSON.stringify(contextFilter.value ?? null) } });
                setFiltersOpen(true);
            }
            setContextFilter(null);
        }}>Apply exact filter</Button><Button variant="outline" onClick={() => {
            if (contextFilter) {
                const filters = { ...query.filters };
                delete filters[contextFilter.key];
                update({ filters });
            }
            setContextFilter(null);
        }}>Clear column filter</Button></DialogContent></Dialog>
        <Dialog open={Boolean(detail)} onOpenChange={next => {
            if (!next)
                setDetail(null);
        }}><DialogContent className="evidence-dialog"><DialogHeader><DialogTitle>{String(detail?.title || detail?.name || 'Source evidence')}</DialogTitle><DialogDescription>Retained source records and interpretations; viewing a record does not establish task acceptance.</DialogDescription></DialogHeader>{sourcePending ? <p>Loading source…</p> : source ? <pre>{JSON.stringify(source, null, 2)}</pre> : Array.isArray(detail?.event_ids) ? <DataTable id={id + '-evidence'} kind="steps" extra={{ ids: detail.event_ids.join(',') }}/> : Array.isArray(detail?.task_ids) ? <DataTable id={id + '-tasks'} kind="marked" extra={{ task_ids: detail.task_ids.join(',') }}/> : <pre>{JSON.stringify(detail, null, 2)}</pre>}</DialogContent></Dialog>
 </div>;
}
function RowActions({ kind, row, onSaved, onInspect }: {
    kind: string;
    row: Row;
    onSaved: () => void;
    onInspect: () => void;
}) {
    const [error, setError] = useState('');
    const change = async (action: string, values: Record<string, unknown>) => {
        try {
            await mutate(action, values);
            onSaved();
        }
        catch (e) {
            setError(e instanceof Error ? e.message : 'Change failed');
        }
    };
    if (kind === 'rules' || kind === 'categorization') {
        const fields: FormField[] = kind === 'rules' ? [{ key: 'name', label: 'Name', value: row.name, required: true }, { key: 'mode', label: 'Mode', value: row.mode, options: modeOptions }, { key: 'config', label: 'Trigger configuration', type: 'json', value: row.config }, { key: 'message', label: 'Message', type: 'textarea', value: row.message }] : [{ key: 'name', label: 'Name', value: row.name, required: true }, { key: 'pattern', label: 'Literal operation pattern', value: row.pattern, required: true }, { key: 'category', label: 'Category', value: row.category, required: true }, { key: 'activity_type', label: 'Activity type', value: row.activity_type }, { key: 'priority', label: 'Rule order', type: 'number', value: row.priority }];
        return <div className="row-actions"><MutationDialog action={kind === 'rules' ? 'rule' : 'categorization'} title={'Edit ' + String(row.name)} fields={fields} values={{ id: row.id }} onSaved={onSaved}><Button variant="outline" size="sm">Edit</Button></MutationDialog>{!row.builtin && <MutationDialog action={kind === 'rules' ? 'delete-rule' : 'delete-categorization'} title={'Delete ' + String(row.name) + '?'} description="The existing audit record and historical firings are preserved." values={{ id: row.id }} destructive onSaved={onSaved}><Button variant="ghost" size="sm">Delete</Button></MutationDialog>}</div>;
    }
    if (kind === 'live')
        return <div className="row-actions"><MutationDialog action="note" title="Send a steering note" description="The note is delivered once on the session's next authenticated hook request." fields={[{ key: 'message', label: 'Note', type: 'textarea', required: true }]} values={{ session_id: row.id }} onSaved={onSaved}><Button variant="outline" size="sm">Send note</Button></MutationDialog><Button variant="outline" size="sm" onClick={() => void change('session', { id: row.id, paused: !row.paused })}>{row.paused ? 'Resume' : 'Pause'}</Button>{error && <span role="alert">{error}</span>}</div>;
    if (kind === 'changes')
        return <MutationDialog action="delete-change" title={'Delete ' + String(row.title) + '?'} values={{ id: row.id }} destructive onSaved={onSaved}><Button variant="ghost" size="sm">Delete</Button></MutationDialog>;
    return <Button variant="ghost" size="icon" aria-label={'Inspect ' + String(row.title || row.name || row.id)} onClick={onInspect}><MoreHorizontal size={15}/></Button>;
}
