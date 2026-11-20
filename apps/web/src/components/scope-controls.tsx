'use client';

import { ChevronLeft, ListFilter } from 'lucide-react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useTransition } from 'react';
import { Button } from '@/components/ui/button';
import { Select, SelectTrigger, SelectContent, SelectValue, SelectItem } from '@/components/ui/select';
import type { DashboardFilters, Scope } from '@/lib/types';

type Choice = { value: string; label: string };

function FilterSelect({ label, all, value, choices, change }: {
    label: string; all: string; value: string; choices: Choice[]; change: (value: string) => void;
}) {
    return <label className="rail-field"><span>{label}</span>
        <Select value={value || '__all'} onValueChange={change}>
            <SelectTrigger aria-label={label}><SelectValue/></SelectTrigger>
            <SelectContent>
                <SelectItem value="__all">{all}</SelectItem>
                {value && !choices.some(choice => choice.value === value) && <SelectItem value={value}>{value}</SelectItem>}
                {choices.map(choice => <SelectItem key={choice.value} value={choice.value}>{choice.label}</SelectItem>)}
            </SelectContent>
        </Select>
    </label>;
}

export function ScopeControls({ scope, projects, workspaces, filters, collapsed, onToggle }: {
    scope: Scope;
    projects: { id: string; name: string }[];
    workspaces: string[];
    filters?: DashboardFilters;
    collapsed: boolean;
    onToggle: () => void;
}) {
    const path = usePathname(), router = useRouter(), params = useSearchParams(), [pending, start] = useTransition();
    const update = (change: Record<string, string>) => {
        const next = new URLSearchParams(params);
        for (const [key, value] of Object.entries(change)) next.set(key, value === '__all' ? '' : value);
        next.delete('day');
        start(() => router.push(`${path}?${next}`, { scroll: false }));
    };
    const field = (key: string) => (value: string) => update({ [key]: value });
    const visibleFilters = filters || { models: [], harnesses: [], work: [] };
    const canClear = Boolean(scope.workspace || scope.project || scope.model || scope.harness || scope.task);

    return <aside className="dashboard-filters" aria-label="Dashboard filters" aria-busy={pending}>
        <div className="filter-rail-inner">
            <div className="filter-heading">
                {!collapsed && <h2>Filters</h2>}
                <Button variant="ghost" size="icon" onClick={onToggle} aria-label={collapsed ? 'Expand filters' : 'Collapse filters'} aria-expanded={!collapsed}>
                    {collapsed ? <ListFilter size={16}/> : <ChevronLeft size={15}/>}
                </Button>
            </div>
            {!collapsed && <div className="filter-fields">
                <FilterSelect label="Workspace" all="All workspaces" value={scope.workspace} choices={workspaces.map(value => ({ value, label: value.split('/').filter(Boolean).at(-1) || value }))} change={field('workspace')}/>
                <FilterSelect label="Project" all="All projects" value={scope.project} choices={projects.map(({ id, name }) => ({ value: id, label: name }))} change={field('project')}/>
                {filters && <>
                    <FilterSelect label="Model" all="All models" value={scope.model || ''} choices={visibleFilters.models.map(value => ({ value, label: value }))} change={field('scopeModel')}/>
                    <FilterSelect label="Work item" all="All work" value={scope.task || ''} choices={visibleFilters.work.map(({ id, title }) => ({ value: id, label: title }))} change={field('work')}/>
                    <div className="rail-field">
                        <span id="harness-label">Harness</span>
                        <div className="harness-list" role="group" aria-labelledby="harness-label">
                            <button type="button" aria-pressed={!scope.harness} onClick={() => field('harness')('')}>All harnesses</button>
                            {visibleFilters.harnesses.map(({ name, sessions }) => <button type="button" key={name} aria-pressed={scope.harness === name} onClick={() => field('harness')(name)}>
                                <span>{name}</span><small>{sessions.toLocaleString()}</small>
                            </button>)}
                        </div>
                    </div>
                </>}
                <div className="rail-field">
                    <span>Range</span>
                    <div className="filter-range" role="group" aria-label="Date range">
                        {['1d', '7d', '30d', '90d', 'all'].map(value => <Button key={value} variant="outline" size="sm" aria-pressed={scope.range === value} onClick={() => field('range')(value)}>{value === 'all' ? 'All' : value}</Button>)}
                    </div>
                </div>
                {(path === '/timeline' || path === '/logs') && <FilterSelect label="Timezone" all="UTC" value={scope.timezone} choices={[...new Set(['UTC', scope.timezone, 'Europe/Amsterdam', 'America/New_York'])].map(value => ({ value, label: value }))} change={field('timezone')}/>}
                {canClear && <Button className="clear-scope" variant="outline" size="sm" onClick={() => update({ workspace: '', project: '', scopeModel: '', harness: '', work: '' })}>Clear filters</Button>}
            </div>}
        </div>
    </aside>;
}
