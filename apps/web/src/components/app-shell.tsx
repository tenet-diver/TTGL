'use client';
import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { Activity, ChartNoAxesCombined, RefreshCw } from 'lucide-react';
import type { ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from './theme-toggle';
import { useViewPreferences } from './use-view-preferences';
const groups = [{ name: 'Analysis', items: [['/', 'Overall activity'], ['/tasks', 'Task activity'], ['/grouping', 'Task grouping'], ['/tools', 'Tool usage'], ['/costs', 'Cost & tokens'], ['/timeline', 'Activity timeline'], ['/agents', 'Agents'], ['/process', 'Process map'], ['/entities', 'Entities'], ['/outcomes', 'Outcomes'], ['/knowledge', 'Knowledge']] }, { name: 'Optimize', items: [['/suggestions', 'Suggestions'], ['/impact', 'Impact'], ['/experiments', 'Experiments'], ['/experiences', 'Experiences'], ['/delegation', 'Delegation'], ['/experience-results', 'Experience results']] }, { name: 'Steer', items: [['/live', 'Live sessions'], ['/live/rules', 'Steering rules']] }, { name: 'Configure', items: [['/categorization', 'Categorization'], ['/data', 'Data list'], ['/jobs', 'Mining jobs'], ['/pricing', 'Pricing']] }];
export function AppShell({ children }: {
    children: ReactNode;
}) {
    const path = usePathname(), params = useSearchParams(), ready = useViewPreferences();
    const suffix = new URLSearchParams();
    for (const key of ['workspace', 'project', 'range', 'timezone'])
        if (params.get(key))
            suffix.set(key, params.get(key)!);
    return <div className="app-shell"><a className="skip-link" href="#content">Skip to content</a><aside className="sidebar"><Link href="/" className="brand"><span><ChartNoAxesCombined size={18}/></span><div>Observatory<small>Coding-agent usage</small></div></Link><nav aria-label="Main navigation">{groups.map(group => <section key={group.name}><p>{group.name}</p>{group.items.map(([href, label]) => <Link key={href} href={href + (suffix.size ? '?' + suffix : '')} aria-current={path === href || (href === '/tasks' && path.startsWith('/tasks/')) ? 'page' : undefined}>{label}</Link>)}</section>)}</nav><div className="sidebar-footer"><p><i className="status-dot"/>Native evidence</p><small>PostgreSQL · ClickHouse · Local S3</small><ThemeToggle /></div></aside><main id="content"><div className="mobile-brand"><Activity size={17}/> Observatory<ThemeToggle /></div>{ready ? children : <p className="page-loading" role="status">Restoring your view…</p>}</main></div>;
}
