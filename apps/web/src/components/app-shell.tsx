'use client';

import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import {
    Activity, Bell, Bot, ChartNoAxesCombined, Coins, FileText, FlaskConical, GitPullRequest,
    LayoutGrid, Lightbulb, ListChecks, Radio, Settings, ShieldCheck, TerminalSquare,
    TrendingUp, TriangleAlert, Wrench,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { ThemeToggle } from './theme-toggle';
import { useViewPreferences } from './use-view-preferences';

const groups = [
    { name: '', items: [{ href: '/', label: 'Overview', icon: LayoutGrid }] },
    { name: 'Work', items: [
        { href: '/sessions', label: 'Sessions', icon: TerminalSquare },
        { href: '/turns', label: 'Turns', icon: ListChecks, also: ['/tasks', '/process', '/timeline', '/subtasks', '/trace'] },
        { href: '/delivery', label: 'Delivery', icon: GitPullRequest, also: ['/outcomes', '/grouping'] },
    ] },
    { name: 'Spend', items: [
        { href: '/costs', label: 'Cost', icon: Coins },
        { href: '/agents', label: 'Agents & models', icon: Bot },
    ] },
    { name: 'Behavior', items: [{ href: '/tools', label: 'Tools', icon: Wrench, also: ['/entities'] }] },
    { name: 'Quality', items: [
        { href: '/errors', label: 'Errors', icon: TriangleAlert },
        { href: '/logs', label: 'Logs', icon: FileText },
        { href: '/metrics', label: 'Metrics', icon: TrendingUp },
    ] },
    { name: 'Improve', items: [
        { href: '/suggestions', label: 'Suggestions', icon: Lightbulb },
        { href: '/experiments', label: 'Experiments', icon: FlaskConical, also: ['/experience-results'] },
        { href: '/impact', label: 'Impact', icon: TrendingUp },
        { href: '/alerts', label: 'Alerts', icon: Bell },
    ] },
    { name: 'Steer', items: [
        { href: '/live', label: 'Live sessions', icon: Radio },
        { href: '/live/rules', label: 'Rules', icon: ShieldCheck },
    ] },
];

export const dashboardScopeKeys = ['workspace', 'project', 'range', 'timezone', 'scopeModel', 'harness', 'work'] as const;

export function AppShell({ children }: { children: ReactNode }) {
    const path = usePathname(), params = useSearchParams(), ready = useViewPreferences();
    const scope = new URLSearchParams();
    for (const key of dashboardScopeKeys) {
        const value = params.get(key);
        if (value) scope.set(key, value);
    }
    const scoped = (href: string) => href + (scope.size ? '?' + scope : '');
    const inside = (href: string) => path === href || (href !== '/' && href !== '/live' && path.startsWith(href + '/'));
    const settings = ['/settings', '/data', '/jobs', '/pricing', '/categorization', '/agent-context', '/memory', '/knowledge', '/experiences', '/delegation'].includes(path);

    return <div className="app-shell project-shell">
        <a className="skip-link" href="#content">Skip to content</a>
        <aside className="sidebar">
            <Link href={scoped('/')} className="brand">
                <span><ChartNoAxesCombined size={18}/></span>
                <div>Observatory<small>Agent analytics</small></div>
            </Link>
            <nav aria-label="Main navigation">
                {groups.map(group => <section key={group.name}>
                    {group.name && <p>{group.name}</p>}
                    {group.items.map(({ href, label, icon: Icon, also }) => <Link key={href} href={scoped(href)}
                        aria-current={inside(href) || also?.some(inside) ? 'page' : undefined}>
                        <Icon size={15} aria-hidden="true"/>{label}
                    </Link>)}
                </section>)}
            </nav>
            <div className="sidebar-footer">
                <p><i className="status-dot"/>Local evidence</p>
                <div className="sidebar-settings">
                    <Link href={scoped('/settings')} aria-current={settings ? 'page' : undefined}><Settings size={15}/>Settings</Link>
                    <ThemeToggle/>
                </div>
            </div>
        </aside>
        <main id="content">
            <div className="mobile-brand"><Activity size={17}/> Observatory<ThemeToggle/></div>
            {ready ? children : <p className="page-loading" role="status">Restoring your view…</p>}
        </main>
    </div>;
}
