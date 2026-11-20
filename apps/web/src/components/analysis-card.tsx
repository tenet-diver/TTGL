'use client';
import { type ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { useLocalPreference } from './use-local-preference';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';
export function AnalysisCard({ title, description, children, actions, className = '', defaultOpen = true, collapsible = true }: {
    title: string;
    description?: string;
    children: ReactNode;
    actions?: ReactNode;
    className?: string;
    defaultOpen?: boolean;
    collapsible?: boolean;
}) {
    const path = usePathname();
    const [open, setOpen] = useLocalPreference('observatory-card:' + path + ':' + title, defaultOpen, value => typeof value === 'boolean' ? value : defaultOpen);
    if (!collapsible) return <Card className={'analysis-card fixed-panel ' + className}><div className="panel-heading"><h2>{title}</h2>{description && <p className="section-note">{description}</p>}{actions}</div><CardContent>{children}</CardContent></Card>;
    return <Card className={'analysis-card ' + className}><Collapsible open={open} onOpenChange={setOpen}><div className="card-heading"><CollapsibleTrigger asChild><Button variant="ghost" className="card-title" aria-label={`${open ? 'Collapse' : 'Expand'} ${title}`}>{open ? <ChevronDown size={14}/> : <ChevronRight size={14}/>}<h2>{title}</h2></Button></CollapsibleTrigger>{actions && <div className="card-actions">{actions}</div>}</div><CollapsibleContent><CardContent>{description && <p className="section-note">{description}</p>}{children}</CardContent></CollapsibleContent></Collapsible></Card>;
}
