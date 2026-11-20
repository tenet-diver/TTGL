import type { Metadata } from 'next';
import localFont from 'next/font/local';
import { Suspense, type ReactNode } from 'react';
import { AppShell } from '@/components/app-shell';
import './globals.css';
import './project-dashboard.css';
const geist = localFont({ src: '../../../../node_modules/next/dist/next-devtools/server/font/geist-latin.woff2', weight: '100 900', display: 'swap', variable: '--font-observatory-sans' });
const geistMono = localFont({ src: '../../../../node_modules/next/dist/next-devtools/server/font/geist-mono-latin.woff2', weight: '100 900', display: 'swap', variable: '--font-observatory-mono' });
export const metadata: Metadata = { title: { default: 'Observatory', template: '%s · Observatory' }, description: 'Native coding-agent usage, task evidence, optimization and steering.' };
export default function RootLayout({ children }: {
    children: ReactNode;
}) { return <html lang="en" className={`dark ${geist.variable} ${geistMono.variable}`} suppressHydrationWarning><body><Suspense fallback={<main>Loading Observatory…</main>}><AppShell>{children}</AppShell></Suspense></body></html>; }
