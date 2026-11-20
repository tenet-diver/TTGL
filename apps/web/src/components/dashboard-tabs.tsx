'use client';

import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { dashboardScopeKeys } from './app-shell';

const turns = [['/turns', 'Turns'], ['/subtasks', 'Subtasks'], ['/process', 'Process']];
const settings = [['/settings', 'Sources'], ['/grouping', 'Task grouping'], ['/categorization', 'Categorization'], ['/jobs', 'Mining jobs'], ['/pricing', 'Pricing'], ['/agent-context', 'Agent context'], ['/memory', 'Memory'], ['/knowledge', 'Knowledge'], ['/delegation', 'Delegation']];
const tabs: Record<string, string[][]> = {
    sessions: [['/sessions', 'List'], ['/sessions?tab=timeline', 'Timeline']],
    turns, subtasks: turns, process: turns,
    delivery: [['/delivery', 'Work items'], ['/delivery?tab=pull-requests', 'Pull requests'], ['/delivery?tab=flow', 'Flow'], ['/delivery?tab=bottlenecks', 'Bottlenecks']],
    tools: [['/tools', 'Overview'], ['/tools?tab=targets', 'Targets'], ['/tools?tab=mcp', 'MCP usage']],
    errors: [['/errors', 'Most common'], ['/errors?tab=all', 'All failures']],
    alerts: [['/alerts', 'Rules'], ['/alerts?tab=history', 'Firing history']],
    experiments: [['/experiments', 'Registry'], ['/experiments?tab=comparison', 'Comparison'], ['/experiments?tab=overhead', 'Research overhead'], ['/experience-results', 'Experience studies']],
    'experience-results': [['/experiments', 'Registry'], ['/experiments?tab=comparison', 'Comparison'], ['/experiments?tab=overhead', 'Research overhead'], ['/experience-results', 'Experience studies']],
    ...Object.fromEntries(settings.map(([href]) => [href.slice(1), settings])),
    memory: [['/memory', 'Inventory'], ['/memory?tab=usage', 'Usage'], ['/agent-context', 'Agent context']],
};

export function scopedHref(href: string, params: Pick<URLSearchParams, 'get'>) {
    if (!href.startsWith('/') || href.startsWith('//')) return href;
    const [path, query = ''] = href.split('?');
    const scope = new URLSearchParams(query);
    for (const key of dashboardScopeKeys) {
        const value = params.get(key);
        if (value && !scope.has(key)) scope.set(key, value);
    }
    return path + (scope.size ? '?' + scope : '');
}

export function DashboardTabs({ view }: { view: string }) {
    const path = usePathname(), params = useSearchParams();
    if (!tabs[view] || (view === 'sessions' && params.get('session'))) return null;
    return <nav className="dashboard-tabs" aria-label={view === 'turns' ? 'Work analysis' : 'Page views'}>
        {tabs[view].map(([href, label]) => {
            const [target, query = ''] = href.split('?');
            const active = path === target && (params.get('tab') || '') === (new URLSearchParams(query).get('tab') || '');
            return <Link key={href} href={scopedHref(href, params)} aria-current={active ? 'page' : undefined}>{label}</Link>;
        })}
    </nav>;
}
