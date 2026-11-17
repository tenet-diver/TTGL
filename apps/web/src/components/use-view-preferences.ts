'use client';
import { useEffect, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { readJson, writeLocal, restoreView, scopeKey, viewFilterKey } from '@/lib/view-preferences';
export function useViewPreferences() {
    const path = usePathname(), params = useSearchParams(), router = useRouter(), search = params.toString();
    const identity = path + '?' + search, [readyFor, setReadyFor] = useState<string | null>(null);
    useEffect(() => {
        // Detail pages already scope their evidence to the task; keep their URL filters transient.
        if (path.startsWith('/tasks/')) { setReadyFor(identity); return; }
        const restored = restoreView(path, new URLSearchParams(search), readJson(scopeKey), readJson(viewFilterKey(path)));
        writeLocal(scopeKey, JSON.stringify(restored.scope));
        writeLocal(viewFilterKey(path), JSON.stringify(restored.filters));
        const target = restored.query.toString();
        if (target !== search) { router.replace(path + '?' + target, { scroll: false }); return; }
        setReadyFor(identity);
    }, [identity, path, search, router]);
    return readyFor === identity;
}
