'use client';
import { Button } from '@/components/ui/button';
export default function ErrorPage({ reset }: {
    error: Error;
    reset: () => void;
}) { return <div role="alert" className="storage-error"><h1>This view could not load</h1><p>Existing records are preserved. Retry the view or check the data services.</p><Button onClick={reset}>Retry</Button></div>; }
