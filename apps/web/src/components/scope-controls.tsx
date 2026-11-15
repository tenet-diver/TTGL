'use client';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useTransition } from 'react';
import { Button } from '@/components/ui/button';
import { Select, SelectTrigger, SelectContent, SelectValue, SelectItem } from '@/components/ui/select';
import type { Scope } from '@/lib/types';
export function ScopeControls({ scope, projects, workspaces }: {
    scope: Scope;
    projects: {
        id: string;
        name: string;
    }[];
    workspaces: string[];
}) {
    const path = usePathname(), router = useRouter(), params = useSearchParams(), [pending, start] = useTransition();
    const update = (key: string, value: string) => {
        const next = new URLSearchParams(params);
        if (value && value !== '__all')
            next.set(key, value);
        else
            next.delete(key);
        start(() => router.push(path + '?' + next, { scroll: false }));
    };
    return <div className="scope-controls" aria-busy={pending}><label><span>Project</span><Select value={scope.project || '__all'} onValueChange={v => update('project', v)}><SelectTrigger aria-label="Project"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="__all">All projects</SelectItem>{projects.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent></Select></label><label><span>Workspace</span><Select value={scope.workspace || '__all'} onValueChange={v => update('workspace', v)}><SelectTrigger aria-label="Workspace"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="__all">All workspaces</SelectItem>{workspaces.map(w => <SelectItem key={w} value={w}>{w}</SelectItem>)}</SelectContent></Select></label><div className="range-control"><span>Range</span><div className="segmented" role="group" aria-label="Date range">{['1d', '7d', '30d', '90d', 'all'].map(value => <Button key={value} variant="ghost" size="sm" aria-pressed={scope.range === value} onClick={() => update('range', value)}>{value === 'all' ? 'All' : value}</Button>)}</div></div>{path === '/timeline' && <label><span>Timezone</span><Select value={scope.timezone} onValueChange={v => update('timezone', v)}><SelectTrigger aria-label="Display timezone"><SelectValue /></SelectTrigger><SelectContent>{[...new Set(['UTC', scope.timezone, 'Europe/Amsterdam', 'America/New_York'])].map(zone => <SelectItem key={zone} value={zone}>{zone}</SelectItem>)}</SelectContent></Select></label>}</div>;
}
