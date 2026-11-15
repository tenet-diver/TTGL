import { notFound } from 'next/navigation';
import { Dashboard } from '@/components/dashboard';
import { TaskDetail } from '@/components/task-detail';
import { pageData, routes } from '@/lib/pages';
import { scopeFrom } from '@/lib/domain';
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';
export default async function Page({ params, searchParams }: {
    params: Promise<{
        path?: string[];
    }>;
    searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
    const path = (await params).path || [], raw = await searchParams, search = new URLSearchParams(Object.entries(raw).flatMap(([k, v]) => typeof v === 'string' ? [[k, v]] : []));
    if (path[0] === 'tasks' && path[1])
        return <TaskDetail id={path[1]}/>;
    if (path.length > 1 && path.join('/') !== 'live/rules')
        notFound();
    const view = path.length ? path.join('/') === 'live/rules' ? 'rules' : path[0] : 'overview';
    if (!routes[view])
        notFound();
    try {
        const scope = scopeFrom(search), data = await pageData(view, scope, search);
        return <Dashboard key={view} view={view} data={data} scope={scope}/>;
    }
    catch {
        return <div className="storage-error" role="alert"><h1>{routes[view].title}</h1><p>The data services are unavailable or this scope exceeds the analysis limit.</p><p>Start PostgreSQL and ClickHouse, apply the numbered migrations, or narrow the date/workspace scope. Existing data is preserved.</p><a href="/api/health">Check service health</a></div>;
    }
}
