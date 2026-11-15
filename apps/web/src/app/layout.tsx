import type { Metadata } from 'next';
import { Suspense, type ReactNode } from 'react';
import { AppShell } from '@/components/app-shell';
import './globals.css';
export const metadata: Metadata = { title: { default: 'Observatory', template: '%s · Observatory' }, description: 'Native coding-agent usage, task evidence, optimization and steering.' };
export default function RootLayout({ children }: {
    children: ReactNode;
}) { return <html lang="en" className="dark" suppressHydrationWarning><body><Suspense fallback={<main>Loading Observatory…</main>}><AppShell>{children}</AppShell></Suspense></body></html>; }
